from __future__ import annotations

import io
import logging
import os
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

try:  # lecture synchrone du modèle stocké en base
    import psycopg2
except Exception:  # pragma: no cover - dépendance optionnelle
    psycopg2 = None

FEATURE_COLUMNS = [
    "duree_minutes",
    "heure_decimale",
    "is_nuit",
    "is_transfrontalier",
    "code_pays_dep",
    "code_pays_arr",
]

logger = logging.getLogger(__name__)

_model_cache: dict[str, Any] = {}

_REQUIRED_KEYS = {"pipeline", "label_encoder", "class_names"}


def _validate_artifact(artifact: Any) -> dict[str, Any]:
    if not isinstance(artifact, dict):
        raise ValueError("Format d'artefact modèle invalide: dict attendu.")
    missing = _REQUIRED_KEYS.difference(artifact)
    if missing:
        raise ValueError(f"Artefact incomplet, clés manquantes: {sorted(missing)}")
    return artifact


def _find_model_path() -> Path:
    env_path = os.getenv("MODEL_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p
        logger.warning("MODEL_PATH env var pointe vers un fichier inexistant: %s", env_path)

    candidates = [
        Path("artifacts/member3/best_model.joblib"),
        Path("../ia-mspr-/artifacts/member3/best_model.joblib"),
        Path("artifacts/member2/best_model.joblib"),
        Path("../ia-mspr-/artifacts/member2/best_model.joblib"),
    ]
    for candidate in candidates:
        if candidate.exists():
            logger.info("Modèle trouvé: %s", candidate)
            return candidate

    raise FileNotFoundError(
        "Aucun fichier modèle trouvé. "
        "Entraînez le modèle (train_from_db.py / member2_ml.py) "
        "ou définissez MODEL_PATH, ou alimentez la table model_artifact."
    )


def _load_from_db(force_reload: bool = False) -> bool:
    """Charge le dernier modèle actif depuis ``model_artifact``. Recharge à chaud
    lorsque l'``id_model`` en base est plus récent que celui en cache.

    Retourne ``True`` si un modèle issu de la base est disponible en cache.
    """
    url = os.getenv("DATABASE_URL")
    if not url or psycopg2 is None:
        return False
    try:
        conn = psycopg2.connect(url)
    except Exception as exc:
        logger.warning("Base indisponible pour le chargement du modèle (%s).", exc)
        return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id_model FROM public.model_artifact "
                "WHERE is_active ORDER BY id_model DESC LIMIT 1"
            )
            row = cur.fetchone()
            if not row:
                return False
            latest_id = int(row[0])
            if not force_reload and _model_cache.get("id_model") == latest_id and "artifact" in _model_cache:
                return True  # déjà à jour
            cur.execute(
                "SELECT id_model, model_name, created_at, metrics, artifact "
                "FROM public.model_artifact WHERE id_model = %s",
                (latest_id,),
            )
            id_model, model_name, created_at, metrics, artifact = cur.fetchone()
        obj = _validate_artifact(joblib.load(io.BytesIO(bytes(artifact))))
        _model_cache["artifact"] = obj
        _model_cache["id_model"] = int(id_model)
        _model_cache["path"] = f"db:model_artifact#{id_model}"
        _model_cache["meta"] = {
            "id_model": int(id_model),
            "model_name": model_name or obj.get("model_name", "?"),
            "created_at": created_at.isoformat() if created_at else None,
            "metrics": metrics,
            "source": "database",
        }
        logger.info("Modèle '%s' chargé depuis la base (id_model=%s).", model_name, id_model)
        return True
    except Exception as exc:
        logger.warning("Échec du chargement du modèle depuis la base (%s).", exc)
        return False
    finally:
        conn.close()


def load_model(force_reload: bool = False) -> dict[str, Any]:
    # 1. priorité à la base (modèle réentraîné), avec rechargement à chaud
    if _load_from_db(force_reload):
        return _model_cache["artifact"]

    # 2. repli fichier (dev/local, ou base sans modèle) — on garde le cache existant
    if force_reload or "artifact" not in _model_cache:
        model_path = _find_model_path()
        artifact = _validate_artifact(joblib.load(model_path))
        _model_cache["artifact"] = artifact
        _model_cache["id_model"] = None
        _model_cache["path"] = str(model_path)
        _model_cache["meta"] = {
            "id_model": None,
            "model_name": artifact.get("model_name", "?"),
            "created_at": None,
            "metrics": None,
            "source": "file",
        }
        logger.info("Modèle '%s' chargé depuis %s", artifact.get("model_name", "?"), model_path)
    return _model_cache["artifact"]


def get_model_source() -> str:
    return _model_cache.get("path", "non chargé")


def get_model_info() -> dict[str, Any]:
    """Métadonnées du modèle actif (pour GET /model/info)."""
    try:
        load_model()
    except FileNotFoundError:
        return {"loaded": False, "source": None}
    meta = dict(_model_cache.get("meta") or {})
    meta["loaded"] = True
    meta["source"] = meta.get("source") or get_model_source()
    return meta


def predict(payload: list[dict[str, Any]]) -> dict[str, Any]:
    artifact = load_model()
    pipeline = artifact["pipeline"]
    label_encoder = artifact["label_encoder"]
    class_names: list[str] = artifact["class_names"]

    frame = pd.DataFrame(payload)
    missing_cols = [c for c in FEATURE_COLUMNS if c not in frame.columns]
    if missing_cols:
        raise ValueError(f"Colonnes manquantes dans le payload: {missing_cols}")
    frame = frame[FEATURE_COLUMNS].copy()

    proba = pipeline.predict_proba(frame)
    pred_idx = np.argmax(proba, axis=1)
    predictions = label_encoder.inverse_transform(pred_idx)

    results = []
    for i, pred in enumerate(predictions):
        proba_dict = {cls: float(proba[i, j]) for j, cls in enumerate(class_names)}
        item: dict[str, Any] = {
            "prediction": str(pred),
            "probabilities": proba_dict,
        }
        for cls in class_names:
            safe_key = f"proba_{cls}"
            item[safe_key] = proba_dict[cls]
        # Ensure the three expected keys exist (fill with 0.0 if a class is absent)
        for default_cls in ["non_pertinent", "substitution_difficile", "substitution_possible"]:
            item.setdefault(f"proba_{default_cls}", 0.0)
        results.append(item)

    return {
        "results": results,
        "model_name": artifact.get("model_name", "unknown"),
        "count": len(results),
        "model_source": get_model_source(),
    }
