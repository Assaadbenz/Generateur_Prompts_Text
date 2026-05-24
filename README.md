# Générateur de Prompts

Une application complète pour générer et optimiser des prompts pour modèles IA.

## Architecture

- **Backend**: FastAPI (Python) - API RESTful
- **Frontend**: Streamlit (Python) - Interface utilisateur
- **Base de données**: SQLite

## Installation

1. Installer les dépendances:
```bash
pip install -r requirements.txt
```

## Démarrage

### 1. Démarrer le backend
```bash
python backend/main.py
```

Ou avec uvicorn:
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

L'API sera disponible à: http://localhost:8000

### 2. Démarrer le frontend (dans un autre terminal)
```bash
streamlit run frontend/app.py
```

L'interface Streamlit sera disponible à: http://localhost:8501

## Fonctionnalités

### Génération de Prompts
- Créez des prompts en fournissant:
  - Rôle: Le rôle du modèle
  - Tâche: La tâche à accomplir
  - Contexte: Le contexte de la tâche
  - Ton: Le ton souhaité

### Optimisation
- Optimisez les prompts existants
- Obtenez un score de qualité (0-100) basé sur:
  - Présence de mots-clés: "Rôle", "Contexte", "Format"
  - Longueur du prompt

### Historique
- Consultez tous les prompts sauvegardés
- Supprimez les prompts indésirables

## Structure du projet

```
Projet_Generateur_Prompts/
├── setup_project.py           # Script de configuration
├── requirements.txt           # Dépendances Python
├── prompts.db                # Base de données SQLite (créée à la première exécution)
├── backend/
│   ├── __init__.py
│   ├── main.py              # API FastAPI
│   ├── database.py          # Gestion SQLite
│   └── optimizer.py         # Logique d'optimisation
└── frontend/
    └── app.py               # Interface Streamlit
```

## API Endpoints

- `GET /` - Endpoint racine
- `POST /generate` - Générer un prompt
- `POST /optimize` - Optimiser un prompt
- `GET /prompts` - Récupérer tous les prompts
- `GET /prompts/{id}` - Récupérer un prompt spécifique
- `POST /prompts/save` - Sauvegarder un prompt
- `DELETE /prompts/{id}` - Supprimer un prompt

## Notes

- La base de données SQLite (`prompts.db`) sera créée automatiquement
- Le CORS est configuré pour permettre les requêtes depuis Streamlit
- En mode test, l'API Hugging Face retourne des résultats fictifs
