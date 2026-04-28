# ObRail Europe – API REST & Base de données
## MSPR TPRE612 – Bloc E6.1

---

## Structure du projet

```
obrail/
├── mpd_obrail.sql       # Schéma PostgreSQL complet (MPD)
├── main.py              # API FastAPI
├── requirements.txt     # Dépendances Python
└── README.md
```

---

## Installation & lancement

### 1. Base de données PostgreSQL

```bash
# Créer la base
psql -U postgres -c "CREATE DATABASE obrail_db;"
psql -U postgres -c "CREATE USER obrail_user WITH PASSWORD 'obrail_pass';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE obrail_db TO obrail_user;"

# Charger le schéma
psql -U obrail_user -d obrail_db -f mpd_obrail.sql
```

### 2. API FastAPI

```bash
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Documentation interactive

- Swagger UI : http://localhost:8000/docs
- ReDoc      : http://localhost:8000/redoc

---

## Endpoints principaux

| Méthode | Endpoint                       | Description                              |
|---------|--------------------------------|------------------------------------------|
| GET     | `/`                            | Informations générales de l'API          |
| GET     | `/trajets`                     | Liste des trajets (filtres disponibles)  |
| GET     | `/trajets/{id}`                | Détail d'un trajet                       |
| GET     | `/services`                    | Services ferroviaires                    |
| GET     | `/gares`                       | Gares (filtre pays / ville)              |
| GET     | `/emissions/stats`             | Stats CO₂ par type de train              |
| GET     | `/emissions/trajets/{id}`      | Émissions d'un trajet                    |
| GET     | `/imports`                     | Historique ETL + qualité                 |
| GET     | `/operateurs`                  | Opérateurs et nb de services             |
| GET     | `/sources`                     | Sources open data utilisées              |
| GET     | `/dashboard`                   | KPIs tableau de bord                     |

---

## Exemples de requêtes

```bash
# Trajets de nuit SNCF
curl "http://localhost:8000/trajets?type_train=nuit&operateur=SNCF"

# Gares françaises
curl "http://localhost:8000/gares?code_pays=FR"

# Statistiques émissions
curl "http://localhost:8000/emissions/stats"

# Tableau de bord
curl "http://localhost:8000/dashboard"

# Imports avec score qualité
curl "http://localhost:8000/imports?statut=succès"
```

---

## Variables d'environnement

Créer un fichier `.env` à la racine :

```
DATABASE_URL=postgresql://obrail_user:obrail_pass@localhost:5432/obrail_db
```

Et modifier `main.py` :
```python
from dotenv import load_dotenv
import os
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
```

---

## Conformité RGPD

- Aucune donnée personnelle n'est collectée ou stockée.
- Les sources de données sont exclusivement open data.
- Traçabilité complète via `historique_import`.
- Documentation transparente des sources et transformations.
