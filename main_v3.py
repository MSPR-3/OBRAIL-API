

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import databases

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = "postgresql://obrail_user:test@localhost:5432/obrail_db"
database = databases.Database(DATABASE_URL)

# Pydantic schemas

class TrajetOut(BaseModel):
    id_trajet: str
    id_trajet_source: Optional[str]
    nom_ligne: Optional[str]
    operateur: Optional[str]
    ville_depart: Optional[str]
    gare_depart: Optional[str]
    ville_arrivee: Optional[str]
    gare_arrivee: Optional[str]
    heure_depart: str
    heure_arrivee: str
    duree_minutes: int
    emission_co2_kg: Optional[Decimal]

class GareOut(BaseModel):
    id_gare: str
    nom_officiel: str
    code_pays: str
    type_liaison: str
    ville: str
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]
    nom_pays: Optional[str]

class LigneOut(BaseModel):
    id_ligne: str
    nom_ligne: str

class OperateurOut(BaseModel):
    id_operateur: str
    nom: str
    nb_trajets: int

class LocalisationOut(BaseModel):
    code_pays: str
    nom_pays: str
    ville: str

class ImportOut(BaseModel):
    id_import: int
    date_import: datetime
    nb_lignes_importees: int
    statut: str
    message: Optional[str]

class EmissionStats(BaseModel):
    operateur: Optional[str]
    nb_trajets: int
    emission_moyenne_kg: Optional[Decimal]

class DashboardOut(BaseModel):
    total_trajets: int
    total_gares: int
    total_lignes: int
    total_operateurs: int
    total_pays: int
    derniere_mise_a_jour: Optional[datetime]

class ErrorResponse(BaseModel):
    code: int
    message: str
    detail: Optional[str] = None

# App lifespan

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await database.connect()
        logger.info("PostgreSQL connection established")
    except Exception as e:
        logger.error(f"PostgreSQL connection error: {e}")
        raise
    yield
    await database.disconnect()
    logger.info("PostgreSQL connection closed")

# FastAPI app setup

description = """
ObRail Europe – API de données ferroviaires européennes

Endpoints disponibles :
- Trajets : recherche par ville, opérateur, durée, émissions
- Gares : recherche par pays, ville, type de liaison
- Lignes : lignes ferroviaires avec distances
- Opérateurs : opérateurs ferroviaires européens
- Localisations : référentiel géographique
- Émissions CO₂ : statistiques par opérateur
- Imports : historique ETL
- Dashboard : KPIs globaux

Exemples :
GET /trajets?ville_depart=Paris&ville_arrivee=Berlin
GET /trajets?operateur=SNCF&duree_max=120
GET /gares?code_pays=FR
GET /emissions/stats
GET /dashboard
"""

app = FastAPI(
    title="ObRail Europe API",
    description=description,
    version="2.0.0",
    contact={"name": "ObRail Europe", "email": "data@obrail.eu"},
    license_info={"name": "Open Data – CC BY 4.0"},
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Error handlers

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    logger.warning(f"404 - {request.url}")
    return JSONResponse(status_code=404, content={"code": 404, "message": "Ressource non trouvée", "detail": exc.detail})

@app.exception_handler(422)
async def validation_error_handler(request: Request, exc):
    logger.warning(f"422 - {request.url}")
    return JSONResponse(status_code=422, content={"code": 422, "message": "Paramètre invalide", "detail": "Vérifiez les paramètres"})

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"500 - {request.url} - {str(exc)}")
    return JSONResponse(status_code=500, content={"code": 500, "message": "Erreur serveur interne", "detail": "Une erreur inattendue s'est produite"})

# Validation helpers

def valider_code_pays(code_pays: Optional[str]) -> None:
    if code_pays and len(code_pays) != 2:
        raise HTTPException(status_code=400, detail="code_pays doit être 2 lettres (ex: FR, DE)")

def valider_id_positif(id: int, nom: str) -> None:
    if id <= 0:
        raise HTTPException(status_code=400, detail=f"{nom} doit être un entier positif")

# SQL select for trajets

TRAJET_SELECT = """
    SELECT
        t.id_trajet,
        t.id_trajet_source,
        l.nom_ligne,
        o.nom               AS operateur,
        gd.ville            AS ville_depart,
        gd.nom_officiel     AS gare_depart,
        ga.ville            AS ville_arrivee,
        ga.nom_officiel     AS gare_arrivee,
        t.heure_depart::text,
        t.heure_arrivee::text,
        t.duree_minutes,
        t.emission_co2_kg
    FROM trajet t
    LEFT JOIN ligne l     ON t.id_ligne       = l.id_ligne
    LEFT JOIN operateur o ON t.id_operateur   = o.id_operateur
    LEFT JOIN gare gd     ON t.id_gare_depart = gd.id_gare
    LEFT JOIN gare ga     ON t.id_gare_arrivee= ga.id_gare
"""

# API routes

@app.get("/", tags=["Racine"])
async def root():
    return {
        "api": "ObRail Europe",
        "version": "2.0.0",
        "documentation": "http://localhost:8000/docs",
        "endpoints": ["/trajets", "/gares", "/lignes", "/operateurs", "/localisations", "/emissions/stats", "/imports", "/dashboard"],
    }

# Trajets endpoints

@app.get("/trajets", response_model=list[TrajetOut], tags=["Trajets"], summary="Rechercher des trajets")
async def get_trajets(
    ville_depart: Optional[str] = Query(None, examples=["Paris"]),
    ville_arrivee: Optional[str] = Query(None, examples=["Berlin"]),
    operateur: Optional[str] = Query(None, examples=["SNCF"]),
    code_pays_depart: Optional[str] = Query(None, examples=["FR"]),
    code_pays_arrivee: Optional[str] = Query(None, examples=["DE"]),
    duree_max: Optional[int] = Query(None, ge=1, examples=[480]),
    emission_max: Optional[float] = Query(None, ge=0, description="Émission CO2 max en kg"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Recherche des trajets selon plusieurs critères combinables."""
    valider_code_pays(code_pays_depart)
    valider_code_pays(code_pays_arrivee)
    try:
        conditions, params = [], {"limit": limit, "offset": offset}
        if ville_depart:
            conditions.append("LOWER(gd.ville) LIKE LOWER(:ville_depart)")
            params["ville_depart"] = f"%{ville_depart}%"
        if ville_arrivee:
            conditions.append("LOWER(ga.ville) LIKE LOWER(:ville_arrivee)")
            params["ville_arrivee"] = f"%{ville_arrivee}%"
        if operateur:
            conditions.append("o.nom ILIKE :operateur")
            params["operateur"] = f"%{operateur}%"
        if code_pays_depart:
            conditions.append("gd.code_pays = :code_pays_depart")
            params["code_pays_depart"] = code_pays_depart.upper()
        if code_pays_arrivee:
            conditions.append("ga.code_pays = :code_pays_arrivee")
            params["code_pays_arrivee"] = code_pays_arrivee.upper()
        if duree_max:
            conditions.append("t.duree_minutes <= :duree_max")
            params["duree_max"] = duree_max
        if emission_max is not None:
            conditions.append("t.emission_co2_kg <= :emission_max")
            params["emission_max"] = emission_max
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = await database.fetch_all(f"{TRAJET_SELECT} {where} ORDER BY t.id_trajet LIMIT :limit OFFSET :offset", params)
        logger.info(f"GET /trajets → {len(rows)} résultats")
        return [dict(r) for r in rows]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur GET /trajets : {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération trajets")

@app.get("/trajets/{id_trajet}", response_model=TrajetOut, tags=["Trajets"], summary="Détail d'un trajet")
async def get_trajet(id_trajet: str):
    try:
        row = await database.fetch_one(f"{TRAJET_SELECT} WHERE t.id_trajet = :id", {"id": id_trajet})
        if not row:
            raise HTTPException(status_code=404, detail=f"Trajet {id_trajet} non trouvé")
        return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur GET /trajets/{id_trajet} : {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération trajet")

# Gares endpoints

@app.get("/gares", response_model=list[GareOut], tags=["Gares"], summary="Rechercher des gares")
async def get_gares(
    code_pays: Optional[str] = Query(None, examples=["FR"]),
    ville: Optional[str] = Query(None, examples=["Paris"]),
    type_liaison: Optional[str] = Query(None, description="nationale | internationale | régionale"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Retourne les gares avec coordonnées GPS."""
    valider_code_pays(code_pays)
    if type_liaison and type_liaison not in ["nationale", "internationale", "régionale"]:
        raise HTTPException(status_code=400, detail="type_liaison invalide : nationale | internationale | régionale")
    try:
        conditions, params = [], {"limit": limit, "offset": offset}
        if code_pays:
            conditions.append("g.code_pays = :code_pays")
            params["code_pays"] = code_pays.upper()
        if ville:
            conditions.append("g.ville ILIKE :ville")
            params["ville"] = f"%{ville}%"
        if type_liaison:
            conditions.append("g.type_liaison = :type_liaison")
            params["type_liaison"] = type_liaison
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        query = f"""
            SELECT g.id_gare, g.nom_officiel, g.code_pays, g.type_liaison,
                   g.ville, g.latitude, g.longitude, l.nom_pays
            FROM gare g
            LEFT JOIN localisation l ON g.code_pays = l.code_pays AND g.ville = l.ville
            {where}
            ORDER BY g.code_pays, g.ville
            LIMIT :limit OFFSET :offset
        """
        rows = await database.fetch_all(query=query, values=params)
        logger.info(f"GET /gares → {len(rows)} résultats")
        return [dict(r) for r in rows]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur GET /gares : {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération gares")

@app.get("/gares/{id_gare}", response_model=GareOut, tags=["Gares"], summary="Détail d'une gare")
async def get_gare(id_gare: str):
    try:
        query = """
            SELECT g.id_gare, g.nom_officiel, g.code_pays, g.type_liaison,
                   g.ville, g.latitude, g.longitude, l.nom_pays
            FROM gare g
            LEFT JOIN localisation l ON g.code_pays = l.code_pays AND g.ville = l.ville
            WHERE g.id_gare = :id
        """
        row = await database.fetch_one(query=query, values={"id": id_gare})
        if not row:
            raise HTTPException(status_code=404, detail=f"Gare {id_gare} non trouvée")
        return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur GET /gares/{id_gare} : {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération gare")

# Lignes endpoints

@app.get("/lignes", response_model=list[LigneOut], tags=["Lignes"], summary="Lister les lignes")
async def get_lignes(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    try:
        rows = await database.fetch_all(f"SELECT id_ligne, nom_ligne FROM ligne ORDER BY nom_ligne LIMIT :limit OFFSET :offset", {"limit": limit, "offset": offset})
        logger.info(f"GET /lignes → {len(rows)} résultats")
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Erreur GET /lignes : {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération lignes")

# Opérateurs endpoints

@app.get("/operateurs", response_model=list[OperateurOut], tags=["Opérateurs"], summary="Lister les opérateurs")
async def get_operateurs():
    try:
        query = """
            SELECT o.id_operateur::text AS id_operateur, o.nom, COUNT(t.id_trajet) AS nb_trajets
            FROM operateur o
            LEFT JOIN trajet t ON o.id_operateur = t.id_operateur
            GROUP BY o.id_operateur, o.nom
            ORDER BY nb_trajets DESC
        """
        rows = await database.fetch_all(query=query)
        if not rows:
            raise HTTPException(status_code=404, detail="Aucun opérateur trouvé")
        return [dict(r) for r in rows]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur GET /operateurs : {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération opérateurs")

# Localisations endpoints

@app.get("/localisations", response_model=list[LocalisationOut], tags=["Localisations"], summary="Lister les localisations")
async def get_localisations(
    code_pays: Optional[str] = Query(None, examples=["FR"]),
):
    valider_code_pays(code_pays)
    try:
        conditions, params = [], {}
        if code_pays:
            conditions.append("code_pays = :code_pays")
            params["code_pays"] = code_pays.upper()
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = await database.fetch_all(f"SELECT code_pays, nom_pays, ville FROM localisation {where} ORDER BY nom_pays, ville", params)
        logger.info(f"GET /localisations → {len(rows)} résultats")
        return [dict(r) for r in rows]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur GET /localisations : {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération localisations")

# Émissions endpoints

@app.get("/emissions/stats", response_model=list[EmissionStats], tags=["Émissions CO₂"], summary="Stats émissions par opérateur")
async def get_emission_stats():
    """Statistiques CO₂ agrégées par opérateur."""
    try:
        query = """
            SELECT
                o.nom                  AS operateur,
                COUNT(t.id_trajet)     AS nb_trajets,
                AVG(t.emission_co2_kg) AS emission_moyenne_kg
            FROM trajet t
            LEFT JOIN operateur o ON t.id_operateur = o.id_operateur
            LEFT JOIN ligne l     ON t.id_ligne     = l.id_ligne
            GROUP BY o.nom
            ORDER BY emission_moyenne_kg DESC NULLS LAST
        """
        rows = await database.fetch_all(query=query)
        if not rows:
            raise HTTPException(status_code=404, detail="Aucune donnée d'émission disponible")
        logger.info(f"GET /emissions/stats → {len(rows)} opérateurs")
        return [dict(r) for r in rows]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur GET /emissions/stats : {e}")
        raise HTTPException(status_code=500, detail="Erreur calcul statistiques")

# Imports endpoints

@app.get("/imports", response_model=list[ImportOut], tags=["Imports ETL"], summary="Historique imports ETL")
async def get_imports(
    statut: Optional[str] = Query(None, description="succès | echec | partiel"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    if statut and statut not in ["succès", "echec", "partiel"]:
        raise HTTPException(status_code=400, detail="statut invalide : succès | echec | partiel")
    try:
        conditions, params = [], {"limit": limit, "offset": offset}
        if statut:
            conditions.append("statut = :statut")
            params["statut"] = statut
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = await database.fetch_all(f"SELECT id_import, date_import, nb_lignes_importees, statut, message FROM historique_import {where} ORDER BY date_import DESC LIMIT :limit OFFSET :offset", params)
        logger.info(f"GET /imports → {len(rows)} résultats")
        return [dict(r) for r in rows]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur GET /imports : {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération imports")

# Dashboard endpoint

@app.get("/dashboard", response_model=DashboardOut, tags=["Dashboard"], summary="KPIs globaux")
async def get_dashboard():
    """Indicateurs globaux de la base de données ObRail."""
    try:
        query = """
            SELECT
                (SELECT COUNT(*) FROM trajet)               AS total_trajets,
                (SELECT COUNT(*) FROM gare)                 AS total_gares,
                (SELECT COUNT(*) FROM ligne)                AS total_lignes,
                (SELECT COUNT(*) FROM operateur)            AS total_operateurs,
                (SELECT COUNT(DISTINCT code_pays)
                 FROM localisation)                         AS total_pays,
                (SELECT MAX(date_import)
                 FROM historique_import)                    AS derniere_mise_a_jour
        """
        row = await database.fetch_one(query=query)
        if not row:
            raise HTTPException(status_code=500, detail="Impossible de récupérer les KPIs")
        logger.info("GET /dashboard → OK")
        return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur GET /dashboard : {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération dashboard")