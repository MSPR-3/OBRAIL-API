FROM python:3.11-slim

# libgomp1 : requis par xgboost / lightgbm (désérialisation du modèle réentraîné)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Chemin vers le modèle entraîné
ENV MODEL_PATH=artifacts/member2/best_model.joblib

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
