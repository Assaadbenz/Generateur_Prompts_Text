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

2. Créer le fichier .env (copier de .env.example):
```bash
cp .env.example .env
```

## Démarrage

### Option 1: Démarrer avec le script run.py
```bash
python run.py
```

### Option 2: Démarrer manuellement

Terminal 1 - Backend:
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 - Frontend:
```bash
streamlit run frontend/app.py
```

L'API sera disponible à: http://localhost:8000
L'interface Streamlit sera disponible à: http://localhost:8501

## Tester l'API

Accédez à la documentation interactive: http://localhost:8000/docs

## Exécuter les tests

```bash
python run_tests.py
```

ou

```bash
pytest tests/
```

## Fonctionnalités

### Génération de Prompts
- Créez des prompts en fournissant:
  - Expertise: Domaine d'expertise
  - Mission: Mission du prompt
  - Ton: Ton souhaité
  - Format: Format de sortie
  - Longueur: Longueur du prompt

### Optimisation
- Optimisez les prompts existants
- Obtenez un score de qualité (0-100)

### Historique
- Consultez tous les prompts sauvegardés
- Recherchez parmi les prompts
- Supprimez les prompts indésirables

## Structure du projet

```
Projet_Generateur_Prompts/
├── .env.example              # Configuration template
├── requirements.txt          # Dépendances Python
├── run.py                    # Script de démarrage
├── run_tests.py              # Script de test
├── IMPROVEMENTS.md           # Améliorations du code
├── README.md                 # Cette documentation
├── backend/
│   ├── __init__.py
│   ├── config.py             # Configuration
│   ├── logger.py             # Logging
│   ├── main.py               # API FastAPI
│   ├── database.py           # Gestion SQLite
│   └── optimizer.py          # Logique d'optimisation
├── frontend/
│   └── app.py                # Interface Streamlit
├── tests/
│   └── test_api.py           # Tests unitaires
└── logs/
    └── app.log               # Logs d'application
```

## Configuration

Voir `.env.example` pour toutes les variables de configuration disponibles.

## Documentation API

### Endpoints principaux

- `GET /` - Vérifier le statut de l'API
- `POST /generate` - Générer un prompt
- `POST /optimize` - Optimiser un prompt
- `GET /prompts` - Récupérer les prompts (avec pagination)
- `GET /prompts/search` - Rechercher des prompts
- `GET /prompts/{id}` - Récupérer un prompt spécifique
- `POST /prompts/save` - Sauvegarder un prompt
- `DELETE /prompts/{id}` - Supprimer un prompt

## Améliorations du code

Le projet inclut plusieurs améliorations importantes:

✅ Configuration management (config.py)
✅ Logging system (logger.py)
✅ Input validation avec Pydantic
✅ Error handling avec HTTP codes appropriés
✅ CORS security (restricted origins)
✅ Database context managers
✅ Comprehensive tests
✅ Environment variable support
✅ Better UI/UX

Pour plus de détails, voir `IMPROVEMENTS.md`.

## Troubleshooting

### L'API n'est pas accessible

1. Vérifiez que le serveur backend est en cours d'exécution
2. Vérifiez que le port 8000 est disponible
3. Vérifiez les logs dans `logs/app.log`

### La base de données ne fonctionne pas

1. Supprimez `prompts.db`
2. Redémarrez l'application
3. Le fichier sera recréé automatiquement

### Les tests échouent

1. Assurez-vous que pytest est installé: `pip install -r requirements.txt`
2. Exécutez: `python -m pytest tests/ -v`
