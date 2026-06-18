"""Client Amadeus Self-Service — métriques vol réelles (durée, prix, CO₂).

Appelé côté serveur uniquement (la clé reste secrète). OAuth2 client_credentials
avec token mis en cache. En l'absence de clé ou de résultat, le routeur bascule
sur le repli ADEME (services/co2.py).
"""
from __future__ import annotations

import logging
import os
import re
import time
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

_token_cache: dict[str, Any] = {}     # {access_token, expires_at}
_iata_cache: dict[str, str] = {}      # keyword -> iataCode


class AmadeusUnavailable(RuntimeError):
    """Clé absente ou Amadeus injoignable -> repli."""


def _base() -> str:
    return os.getenv("AMADEUS_BASE", "test.api.amadeus.com").rstrip("/")


def _creds() -> tuple[str, str]:
    cid, secret = os.getenv("AMADEUS_CLIENT_ID"), os.getenv("AMADEUS_SECRET")
    if not cid or not secret:
        raise AmadeusUnavailable("AMADEUS_CLIENT_ID / AMADEUS_SECRET non définis")
    return cid, secret


async def _get_token(client: httpx.AsyncClient) -> str:
    now = time.time()
    if _token_cache.get("access_token") and _token_cache.get("expires_at", 0) > now + 30:
        return _token_cache["access_token"]
    cid, secret = _creds()
    resp = await client.post(
        f"https://{_base()}/v1/security/oauth2/token",
        data={"grant_type": "client_credentials", "client_id": cid, "client_secret": secret},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = now + int(data.get("expires_in", 1799))
    return _token_cache["access_token"]


async def _resolve_iata(client: httpx.AsyncClient, token: str, keyword: str, country: Optional[str]) -> Optional[str]:
    if not keyword:
        return None
    cache_key = f"{keyword}|{country or ''}".lower()
    if cache_key in _iata_cache:
        return _iata_cache[cache_key]
    params = {"subType": "CITY,AIRPORT", "keyword": keyword, "page[limit]": 5, "sort": "analytics.travelers.score"}
    if country:
        params["countryCode"] = country.upper()
    resp = await client.get(
        f"https://{_base()}/v1/reference-data/locations",
        params=params,
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp.status_code != 200:
        return None
    rows = resp.json().get("data", [])
    # privilégie une ville (CITY) sinon premier aéroport
    code = next((r["iataCode"] for r in rows if r.get("subType") == "CITY"), None)
    if not code and rows:
        code = rows[0].get("iataCode")
    if code:
        _iata_cache[cache_key] = code
    return code


def _iso_duration_to_min(iso: str) -> int:
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?", iso or "")
    if not m:
        return 0
    h = int(m.group(1) or 0)
    mn = int(m.group(2) or 0)
    return h * 60 + mn


async def flight_metrics(
    dep_keyword: str, dep_country: Optional[str], arr_keyword: str, arr_country: Optional[str], date: str
) -> dict[str, Any]:
    """Retourne {prix_eur, duree_min, correspondances, co2_kg|None, dep_iata, arr_iata}.

    Lève AmadeusUnavailable si la clé manque ou aucun vol exploitable.
    """
    _creds()  # lève tôt si pas de clé
    timeout = httpx.Timeout(15.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        token = await _get_token(client)
        dep_iata = await _resolve_iata(client, token, dep_keyword, dep_country)
        arr_iata = await _resolve_iata(client, token, arr_keyword, arr_country)
        if not dep_iata or not arr_iata:
            raise AmadeusUnavailable("IATA introuvable pour le trajet")

        resp = await client.get(
            f"https://{_base()}/v2/shopping/flight-offers",
            params={
                "originLocationCode": dep_iata,
                "destinationLocationCode": arr_iata,
                "departureDate": date,
                "adults": 1,
                "currencyCode": "EUR",
                "max": 5,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status_code != 200:
            raise AmadeusUnavailable(f"flight-offers {resp.status_code}")
        offers = resp.json().get("data", [])
        if not offers:
            raise AmadeusUnavailable("aucun vol")

        # vol le moins cher
        best = min(offers, key=lambda o: float(o["price"]["grandTotal"]))
        itin = best["itineraries"][0]
        segments = itin.get("segments", [])
        duree_min = _iso_duration_to_min(itin.get("duration", ""))
        co2 = 0.0
        for seg in segments:
            for em in seg.get("co2Emissions", []) or []:
                try:
                    co2 += float(em.get("weight", 0))
                except (TypeError, ValueError):
                    pass
        return {
            "prix_eur": round(float(best["price"]["grandTotal"]), 2),
            "duree_min": duree_min,
            "correspondances": max(0, len(segments) - 1),
            "co2_kg": round(co2, 1) if co2 > 0 else None,
            "dep_iata": dep_iata,
            "arr_iata": arr_iata,
        }
