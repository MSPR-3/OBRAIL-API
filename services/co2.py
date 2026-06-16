"""Facteurs d'émission CO₂ (ordre de grandeur ADEME) pour le comparatif modal.

Sert de repli quand Amadeus ne fournit pas le CO₂ d'un vol, et pour le train.
Valeurs en kg CO₂ équivalent par passager.km (incl. forçage radiatif pour l'avion).
"""
from __future__ import annotations

# Train électrifié (moyenne européenne, conservateur). DB ObRail ~0.05 kg/min ≈ utilisé en repli.
RAIL_KG_PER_KM = 0.035
RAIL_KG_PER_MIN = 0.05  # cohérent avec emission_co2_kg de la base (≈ 0.05 × durée)

# Avion court / long courrier (incl. effets hors-CO₂). Seuil 1000 km.
PLANE_SHORT_KG_PER_KM = 0.255
PLANE_LONG_KG_PER_KM = 0.195
PLANE_LONG_THRESHOLD_KM = 1000.0


def co2_rail(distance_km: float | None, duree_min: float | None = None, co2_db: float | None = None) -> float:
    """CO₂ train : privilégie la valeur de la base, sinon distance, sinon durée."""
    if co2_db and co2_db > 0:
        return round(float(co2_db), 1)
    if distance_km and distance_km > 0:
        return round(distance_km * RAIL_KG_PER_KM, 1)
    if duree_min and duree_min > 0:
        return round(duree_min * RAIL_KG_PER_MIN, 1)
    return 0.0


def co2_plane(distance_km: float | None) -> float:
    """CO₂ avion estimé à partir de la distance grand-cercle (repli sans Amadeus)."""
    if not distance_km or distance_km <= 0:
        return 0.0
    factor = PLANE_SHORT_KG_PER_KM if distance_km < PLANE_LONG_THRESHOLD_KM else PLANE_LONG_KG_PER_KM
    return round(distance_km * factor, 1)
