# Multi-stage build pour un conteneur léger et sécurisé
FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système requises
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copie et installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code applicatif
COPY . .

# Création du dossier logs
RUN mkdir -p logs

# Exposition des ports Backend (8000) et Frontend (8501)
EXPOSE 8000 8501

# Script par défaut
CMD ["python", "run.py"]
