from __future__ import annotations

import logging
import math
from datetime import date as date_cls, timedelta
from typing import Optional

from fastapi import APIRouter, Query

from services import avion_service
from services.co2 import co2_plane, co2_rail

router = APIRouter(tags=["IA / Comparatif modal"])
logger = logging.getLogger(__name__)

# Surcoût porte-à-porte de l'avion (accès aéroport + enregistrement + sûreté + transfert).
PORTE_OVERHEAD_MIN = 180
PLANE_SPEED_KMH = 800.0
TRAIN_EUR_PER_KM = 0.12
PLANE_EUR_PER_KM = 0.18


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.asin(math.sqrt(a))


@router.get(
    "/avion/compare",
    summary="Comparatif modal Train vs Avion",
    description=(
        "Compare un trajet ferroviaire à son équivalent aérien (durée porte-à-porte, "
        "prix, CO₂). Données avion réelles via Amadeus si configuré, sinon estimation "
        "documentée (facteurs ADEME). Renvoie aussi le CO₂ évité en prenant le train."
    ),
)
async def compare(
    dep_lat: float = Query(...),
    dep_lng: float = Query(...),
    arr_lat: float = Query(...),
    arr_lng: float = Query(...),
    duree_train_min: float = Query(..., description="Durée du trajet train (minutes)"),
    dep_ville: Optional[str] = Query(None),
    dep_pays: Optional[str] = Query(None),
    arr_ville: Optional[str] = Query(None),
    arr_pays: Optional[str] = Query(None),
    co2_train_db: Optional[float] = Query(None, description="emission_co2_kg connu (base)"),
    date: Optional[str] = Query(None, description="Date vol YYYY-MM-DD (défaut: +14 j)"),
):
    distance_km = round(_haversine_km(dep_lat, dep_lng, arr_lat, arr_lng), 1)
    when = date or (date_cls.today() + timedelta(days=14)).isoformat()

    # --- Train ---
    train = {
        "co2_kg": co2_rail(distance_km, duree_train_min, co2_train_db),
        "duree_min": round(duree_train_min),
        "prix_eur": round(max(15.0, distance_km * TRAIN_EUR_PER_KM)),
        "source": "base" if (co2_train_db and co2_train_db > 0) else "ADEME",
    }

    # --- Avion : Amadeus, sinon repli ADEME ---
    avion: dict = {}
    source = "estimation"
    try:
        m = await avion_service.flight_metrics(
            dep_ville or "", dep_pays, arr_ville or "", arr_pays, when
        )
        source = "amadeus"
        co2 = m["co2_kg"] if m["co2_kg"] is not None else co2_plane(distance_km)
        avion = {
            "co2_kg": co2,
            "duree_min": (m["duree_min"] or 0) + PORTE_OVERHEAD_MIN,
            "duree_vol_min": m["duree_min"],
            "prix_eur": m["prix_eur"],
            "correspondances": m["correspondances"],
            "iata": f'{m["dep_iata"]}→{m["arr_iata"]}',
            "co2_source": "amadeus" if m["co2_kg"] is not None else "ADEME",
        }
    except Exception as exc:  # AmadeusUnavailable ou autre -> repli
        logger.info("Repli estimation avion (%s)", exc)
        vol_min = round(distance_km / PLANE_SPEED_KMH * 60) + 30  # + roulage
        avion = {
            "co2_kg": co2_plane(distance_km),
            "duree_min": vol_min + PORTE_OVERHEAD_MIN,
            "duree_vol_min": vol_min,
            "prix_eur": round(max(40.0, distance_km * PLANE_EUR_PER_KM)),
            "correspondances": 0,
            "iata": None,
            "co2_source": "ADEME",
        }

    avion["source"] = source
    co2_evite = round((avion["co2_kg"] or 0) - (train["co2_kg"] or 0), 1)

    return {
        "distance_km": distance_km,
        "date": when,
        "train": train,
        "avion": avion,
        "co2_evite_kg": co2_evite,
    }
