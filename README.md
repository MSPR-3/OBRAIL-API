# ObRail Europe – API REST & Base de données
## MSPR TPRE612 – Bloc E6.1

---

## Structure du projet

```
ObRail_API/
├── main_v3.py           # API FastAPI (version alignée à la spec API REST)
├── requirements.txt     # Dépendances Python
├── tests/               # Tests API
└── README.md
```

---

## Installation & lancement

### 1. Base de données PostgreSQL

```bash
# Exemple (adapter user/password si besoin)
psql -U postgres -c "CREATE DATABASE obrail_db;"
psql -U postgres -c "CREATE USER obrail_user WITH PASSWORD 'obrail_pass';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE obrail_db TO obrail_user;"
```

### 2. Variables d'environnement

Créer un fichier `.env` à la racine :

```env
DATABASE_URL=postgresql://obrail_user:obrail_pass@localhost:5432/obrail_db
```

### 3. API FastAPI

```bash
pip install -r requirements.txt
uvicorn main_v3:app --reload --host 0.0.0.0 --port 8000
```

### 4. Documentation interactive

- Swagger UI : http://localhost:8000/docs
- ReDoc      : http://localhost:8000/redoc

---

## Endpoints alignés avec la spec

- `GET /trajets` (pagination + filtres)
- `GET /trajets/{id_trajet}`
- `GET /stats/kpi`
- `GET /stats/volumes`
- `GET /stats/comparatif-jour-nuit`
- `GET /stats/co2`
- `GET /stats/top-liaisons`
- `GET /operateurs`
- `GET /lignes`
- `GET /gares`
- `GET /pays`
- `GET /imports`
- `GET /imports/stats`
- `GET /health`

Compatibilité conservée :
- `GET /dashboard`
- `GET /emissions/stats`
- `GET /localisations`

---

## Exemples de requêtes

```bash
curl "http://localhost:8000/trajets?page=1&limit=15&type=jour"
curl "http://localhost:8000/stats/kpi"
curl "http://localhost:8000/stats/volumes?groupby=operateur"
curl "http://localhost:8000/gares?code_pays=FR&search=Paris"
curl "http://localhost:8000/imports?page=1&limit=20&statut=succès"
curl "http://localhost:8000/health"
```
