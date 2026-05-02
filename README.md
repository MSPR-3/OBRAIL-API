# ObRail Europe – API REST

![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0%2B-green)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-blue)

**ObRail Europe API** est une API REST robuste et asynchrone développée avec FastAPI. Elle sert de backend principal pour interagir avec la base de données ferroviaire européenne `ObRail`, fournissant des statistiques, des informations sur les trajets, les gares et les opérateurs.

Ce projet s'inscrit dans le cadre du **MSPR TPRE612 – Bloc E6.1**.

---

## Stack Technique

- **Framework Web** : [FastAPI](https://fastapi.tiangolo.com/) (Asynchrone, performant)
- **Base de données** : PostgreSQL avec l'extension PostGIS
- **ORM / Drivers** : `databases` (asyncpg) et `SQLAlchemy` (core)
- **Serveur WSGI/ASGI** : `Uvicorn`
- **Tests** : `pytest`, `pytest-cov`, `pytest-mock`
- **Conteneurisation** : Docker & Docker Compose

---

## Structure du projet

```text
OBRAIL-API/
├── .env.example         # Exemple de configuration d'environnement
├── docker-compose.yml   # Déploiement Docker de l'API
├── Dockerfile           # Recette de conteneurisation de l'API
├── main.py              # Application principale FastAPI et endpoints
├── pytest.ini           # Configuration de pytest
├── requirements.txt     # Dépendances du projet (API & Tests)
└── tests/               # Dossier contenant tous les tests unitaires
```

---

## Installation & Démarrage

### Option 1 : Avec Docker (Recommandé)

Assurez-vous que la base de données (`OBRAIL-BDD`) est lancée. Si vous utilisez le fichier `docker-compose.yml` présent dans l'API, il se connectera par défaut à la base de données de l'hôte via `host.docker.internal`.

1. **Ouvrir un terminal** dans le répertoire `OBRAIL-API` :
   ```bash
   cd OBRAIL-API
   ```
2. **Lancer le conteneur** :
   ```bash
   docker-compose up -d --build
   ```
3. L'API sera accessible sur **[http://localhost:8000](http://localhost:8000)**.

### Option 2 : En local (Environnement Virtuel Python)

1. **Créer une base de données PostgreSQL** :
   ```sql
   CREATE DATABASE obrail;
   CREATE USER obrail_user WITH PASSWORD 'obrail_pass';
   GRANT ALL PRIVILEGES ON DATABASE obrail TO obrail_user;
   ```
2. **Configurer les variables d'environnement** :
   Copiez `.env.example` en `.env` :
   ```bash
   cp .env.example .env
   ```
   *Modifiez `DATABASE_URL` dans le `.env` pour qu'il corresponde à vos identifiants.*
3. **Créer un environnement virtuel et installer les dépendances** :
   ```bash
   python -m venv venv
   source venv/bin/activate   # Sur Windows : venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. **Lancer l'API via Uvicorn** :
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

---

## Documentation de l'API

FastAPI génère automatiquement la documentation de l'API (OpenAPI) à partir du code source.

- **Swagger UI** (Interactif) : [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc** : [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Endpoints Principaux

L'API expose les ressources suivantes (liste non exhaustive) :

### Système & Santé
- `GET /` : Informations générales de l'API.
- `GET /health` : Vérifie l'état de l'API et de la connexion à la base de données.

### Trajets & Mobilité
- `GET /trajets` : Liste les trajets avec de multiples filtres possibles (pagination, opérateur, ligne, gares, durée, émissions CO2).
- `GET /trajets/{id_trajet}` : Détails complets d'un trajet spécifique.

### Statistiques & KPIs
- `GET /stats/kpi` : Chiffres clés globaux.
- `GET /stats/volumes` : Répartition des volumes par opérateur, ligne, pays ou créneau horaire.
- `GET /stats/comparatif-jour-nuit` : Comparaison des trajets effectués le jour vs la nuit.
- `GET /stats/co2` : Statistiques environnementales sur les émissions.
- `GET /stats/top-liaisons` : Les liaisons les plus fréquentées.

### Référentiels
- `GET /operateurs` : Liste des opérateurs ferroviaires.
- `GET /lignes` : Liste des lignes disponibles.
- `GET /gares` : Liste des gares (filtres possibles par pays et par bounding box géographique).
- `GET /pays` : Liste des pays couverts.

### Importation
- `GET /imports` : Historique des imports de données.
- `GET /imports/stats` : Statistiques de réussite/échec des imports.

---

## Tests

Les tests sont rédigés avec `pytest` et utilisent `pytest-mock` ainsi que `httpx` pour simuler les requêtes HTTP et les accès à la base de données.

Pour lancer la suite de tests et voir la couverture de code :

```bash
pytest --cov=.
```
