#!/usr/bin/env python3
"""
Script de configuration complet pour le projet Générateur de Prompts.
Crée l'arborescence et initialise tous les fichiers avec code fonctionnel.
"""

import os
from pathlib import Path

# Répertoire racine du projet
PROJECT_ROOT = Path(__file__).parent

# Créer les répertoires
backend_dir = PROJECT_ROOT / "backend"
frontend_dir = PROJECT_ROOT / "frontend"

backend_dir.mkdir(exist_ok=True)
frontend_dir.mkdir(exist_ok=True)

# ============================================================================
# 1. requirements.txt
# ============================================================================
requirements_content = """fastapi==0.104.1
uvicorn==0.24.0
streamlit==1.28.1
requests==2.31.0
pydantic==2.4.2
"""

requirements_path = PROJECT_ROOT / "requirements.txt"
with open(requirements_path, "w", encoding="utf-8") as f:
    f.write(requirements_content)
print(f"✓ Créé: {requirements_path}")

# ============================================================================
# 2. backend/database.py
# ============================================================================
database_content = """import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

# Chemin vers la base de données
DB_PATH = Path(__file__).parent.parent / "prompts.db"


def init_db() -> None:
    \"\"\"Initialise la base SQLite avec la table 'prompts'.\"\"\"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prompts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titre TEXT NOT NULL,
        categorie TEXT NOT NULL,
        prompt_text TEXT NOT NULL,
        score INTEGER DEFAULT 0
    )
    ''')
    
    conn.commit()
    conn.close()


def save_prompt(titre: str, categorie: str, prompt_text: str, score: int) -> int:
    \"\"\"
    Sauvegarde un prompt dans la base de données.
    
    Args:
        titre: Titre du prompt
        categorie: Catégorie du prompt
        prompt_text: Contenu du prompt
        score: Score de qualité (0-100)
    
    Returns:
        ID du prompt inséré
    \"\"\"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO prompts (titre, categorie, prompt_text, score)
    VALUES (?, ?, ?, ?)
    ''', (titre, categorie, prompt_text, score))
    
    conn.commit()
    prompt_id = cursor.lastrowid
    conn.close()
    
    return prompt_id


def get_all_prompts() -> List[Dict[str, Any]]:
    \"\"\"Récupère tous les prompts stockés dans la base de données.\"\"\"
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, titre, categorie, prompt_text, score FROM prompts ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_prompt_by_id(prompt_id: int) -> Optional[Dict[str, Any]]:
    \"\"\"Récupère un prompt spécifique par son ID.\"\"\"
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, titre, categorie, prompt_text, score FROM prompts WHERE id = ?', (prompt_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def delete_prompt(prompt_id: int) -> bool:
    \"\"\"Supprime un prompt de la base de données.\"\"\"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM prompts WHERE id = ?', (prompt_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    
    return success
"""

database_path = backend_dir / "database.py"
with open(database_path, "w", encoding="utf-8") as f:
    f.write(database_content)
print(f"✓ Créé: {database_path}")

# ============================================================================
# 3. backend/optimizer.py
# ============================================================================
optimizer_content = """import requests
from typing import Optional


def calculate_quality_score(prompt_text: str) -> int:
    \"\"\"
    Calcule un score de qualité (0-100) basé sur les mots-clés présents.
    
    Mots-clés recherchés: "Rôle", "Contexte", "Format"
    - Chaque mot-clé présent ajoute 30 points
    - Longueur du prompt: +10 points si > 50 caractères
    
    Args:
        prompt_text: Le texte du prompt à évaluer
    
    Returns:
        Score entre 0 et 100
    \"\"\"
    keywords = ["rôle", "contexte", "format"]
    prompt_lower = prompt_text.lower()
    
    score = 0
    for keyword in keywords:
        if keyword in prompt_lower:
            score += 30
    
    # Bonus pour la longueur
    if len(prompt_text) > 50:
        score += 10
    
    # Limiter à 100
    return min(score, 100)


def call_hugging_face_api(prompt_text: str, api_key: Optional[str] = None) -> dict:
    \"\"\"
    Appelle l'API Hugging Face pour générer/améliorer un prompt.
    
    Args:
        prompt_text: Le prompt initial
        api_key: Clé API Hugging Face (optionnelle, à mettre en variable d'env)
    
    Returns:
        Dictionnaire avec la réponse de l'API
    \"\"\"
    # À implémenter avec votre clé API réelle
    # Exemple simplifié qui retourne une structure de test
    
    if not api_key:
        # Retourner une réponse de test
        return {
            "generated_prompt": f"Version optimisée du prompt: {prompt_text}",
            "status": "test_mode"
        }
    
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        # Remplacer avec l'endpoint réel de Hugging Face
        response = requests.post(
            "https://api-inference.huggingface.co/models/...",
            headers=headers,
            json={"inputs": prompt_text},
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }


def optimize_prompt(prompt_text: str) -> dict:
    \"\"\"
    Optimise un prompt en calculant son score et en proposant des améliorations.
    
    Args:
        prompt_text: Le prompt à optimiser
    
    Returns:
        Dictionnaire avec le score et le prompt optimisé
    \"\"\"
    score = calculate_quality_score(prompt_text)
    
    # Logique simple d'optimisation
    optimized = prompt_text
    missing_keywords = []
    
    if "rôle" not in prompt_text.lower():
        missing_keywords.append("Rôle")
    if "contexte" not in prompt_text.lower():
        missing_keywords.append("Contexte")
    if "format" not in prompt_text.lower():
        missing_keywords.append("Format")
    
    return {
        "original_prompt": prompt_text,
        "optimized_prompt": optimized,
        "score": score,
        "missing_keywords": missing_keywords
    }
"""

optimizer_path = backend_dir / "optimizer.py"
with open(optimizer_path, "w", encoding="utf-8") as f:
    f.write(optimizer_content)
print(f"✓ Créé: {optimizer_path}")

# ============================================================================
# 4. backend/main.py
# ============================================================================
main_content = """from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import sys
from pathlib import Path

# Ajouter le répertoire backend au path
sys.path.insert(0, str(Path(__file__).parent))

from database import init_db, save_prompt, get_all_prompts, get_prompt_by_id, delete_prompt
from optimizer import calculate_quality_score, optimize_prompt

# Initialiser l'app FastAPI
app = FastAPI(
    title="Générateur de Prompts API",
    description="API pour générer et optimiser des prompts",
    version="1.0.0"
)

# Configuration CORS pour Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permet toutes les origines
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialiser la base de données au démarrage
init_db()


# ============================================================================
# Modèles Pydantic
# ============================================================================
class PromptRequest(BaseModel):
    role: str
    task: str
    context: str
    tone: str


class PromptResponse(BaseModel):
    titre: str
    prompt_text: str
    score: int


class PromptOptimize(BaseModel):
    prompt_text: str


class PromptStored(BaseModel):
    id: int
    titre: str
    categorie: str
    prompt_text: str
    score: int


# ============================================================================
# Routes
# ============================================================================
@app.get("/")
async def root():
    \"\"\"Endpoint racine pour tester l'API.\"\"\"
    return {"message": "Bienvenue sur l'API Générateur de Prompts"}


@app.post("/generate")
async def generate_prompt(request: PromptRequest) -> Dict[str, Any]:
    \"\"\"
    Génère un prompt basé sur les paramètres fournis.
    
    Args:
        role: Le rôle/personnalité du prompt
        task: La tâche à accomplir
        context: Le contexte de la tâche
        tone: Le ton souhaité
    
    Returns:
        Prompt généré avec son score de qualité
    \"\"\"
    try:
        # Construire le prompt
        prompt_text = f'Rôle: {request.role}\\nTâche: {request.task}\\nContexte: {request.context}\\nTon: {request.tone}'
        
        # Calculer le score
        score = calculate_quality_score(prompt_text)
        
        return {
            "titre": f"Prompt - {request.task[:30]}",
            "prompt_text": prompt_text,
            "score": score
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/optimize")
async def optimize(request: PromptOptimize) -> Dict[str, Any]:
    \"\"\"
    Optimise un prompt existant.
    
    Args:
        prompt_text: Le prompt à optimiser
    
    Returns:
        Prompt optimisé avec score et recommandations
    \"\"\"
    try:
        result = optimize_prompt(request.prompt_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/prompts")
async def list_prompts() -> Dict[str, Any]:
    \"\"\"Récupère la liste de tous les prompts stockés.\"\"\"
    try:
        prompts = get_all_prompts()
        return {
            "total": len(prompts),
            "prompts": prompts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/prompts/{prompt_id}")
async def get_prompt(prompt_id: int) -> Dict[str, Any]:
    \"\"\"Récupère un prompt spécifique par ID.\"\"\"
    try:
        prompt = get_prompt_by_id(prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt non trouvé")
        return prompt
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prompts/save")
async def save_new_prompt(request: PromptResponse) -> Dict[str, Any]:
    \"\"\"Sauvegarde un nouveau prompt dans la base de données.\"\"\"
    try:
        prompt_id = save_prompt(
            titre=request.titre,
            categorie="général",
            prompt_text=request.prompt_text,
            score=request.score
        )
        return {
            "id": prompt_id,
            "message": "Prompt sauvegardé avec succès"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/prompts/{prompt_id}")
async def delete_prompt_route(prompt_id: int) -> Dict[str, Any]:
    \"\"\"Supprime un prompt de la base de données.\"\"\"
    try:
        success = delete_prompt(prompt_id)
        if not success:
            raise HTTPException(status_code=404, detail="Prompt non trouvé")
        return {"message": "Prompt supprimé avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""

main_path = backend_dir / "main.py"
with open(main_path, "w", encoding="utf-8") as f:
    f.write(main_content)
print(f"✓ Créé: {main_path}")

# ============================================================================
# 5. frontend/app.py
# ============================================================================
frontend_content = """import streamlit as st
import requests
from typing import List, Dict, Any

# Configuration de la page
st.set_page_config(
    page_title="Générateur de Prompts",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL de l'API
API_BASE_URL = "http://localhost:8000"


# ============================================================================
# Fonctions utilitaires
# ============================================================================
@st.cache_resource
def get_session_state():
    \"\"\"Initialise les variables de session.\"\"\"
    if 'generated_prompt' not in st.session_state:
        st.session_state.generated_prompt = None
    if 'quality_score' not in st.session_state:
        st.session_state.quality_score = None
    return st.session_state


def fetch_prompts() -> List[Dict[str, Any]]:
    \"\"\"Récupère tous les prompts depuis l'API.\"\"\"
    try:
        response = requests.get(f"{API_BASE_URL}/prompts", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("prompts", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion à l'API: {e}")
    return []


def generate_prompt(role: str, task: str, context: str, tone: str) -> Dict[str, Any]:
    \"\"\"Génère un nouveau prompt via l'API.\"\"\"
    try:
        payload = {
            "role": role,
            "task": task,
            "context": context,
            "tone": tone
        }
        response = requests.post(
            f"{API_BASE_URL}/generate",
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erreur API: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion: {e}")
        return None


def optimize_prompt(prompt_text: str) -> Dict[str, Any]:
    \"\"\"Optimise un prompt via l'API.\"\"\"
    try:
        payload = {"prompt_text": prompt_text}
        response = requests.post(
            f"{API_BASE_URL}/optimize",
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erreur API: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion: {e}")
        return None


def save_prompt_to_db(titre: str, prompt_text: str, score: int) -> bool:
    \"\"\"Sauvegarde un prompt dans la base de données.\"\"\"
    try:
        payload = {
            "titre": titre,
            "prompt_text": prompt_text,
            "score": score
        }
        response = requests.post(
            f"{API_BASE_URL}/prompts/save",
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            st.success("Prompt sauvegardé avec succès! ✓")
            return True
        else:
            st.error(f"Erreur lors de la sauvegarde: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion: {e}")
        return False


def delete_prompt_from_db(prompt_id: int) -> bool:
    \"\"\"Supprime un prompt de la base de données.\"\"\"
    try:
        response = requests.delete(
            f"{API_BASE_URL}/prompts/{prompt_id}",
            timeout=10
        )
        if response.status_code == 200:
            return True
        return False
    except requests.exceptions.RequestException:
        return False


# ============================================================================
# Interface principale
# ============================================================================
st.title("✨ Générateur et Optimiseur de Prompts")
st.markdown("Créez et optimisez des prompts de qualité pour vos modèles IA")

session = get_session_state()

# Créer deux colonnes
col_form, col_result = st.columns([1, 1], gap="medium")

# ============================================================================
# Colonne gauche: Formulaire
# ============================================================================
with col_form:
    st.subheader("📝 Formulaire")
    
    role = st.text_input(
        "Rôle",
        placeholder="ex: Assistant de rédaction",
        help="Quel rôle doit adopter le modèle?"
    )
    
    task = st.text_input(
        "Tâche",
        placeholder="ex: Résumer un article",
        help="Quelle est la tâche principale?"
    )
    
    context = st.text_area(
        "Contexte",
        placeholder="ex: Articles de blog, domaine technique...",
        height=100,
        help="Fournissez le contexte pour une meilleure génération"
    )
    
    tone = st.select_slider(
        "Ton",
        options=["Très formel", "Formel", "Neutre", "Décontracté", "Très décontracté"],
        value="Neutre"
    )
    
    st.markdown("---")
    
    # Boutons
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("🚀 Générer", use_container_width=True, type="primary"):
            if role and task and context:
                with st.spinner("Génération en cours..."):
                    result = generate_prompt(role, task, context, tone)
                    if result:
                        session.generated_prompt = result.get("prompt_text")
                        session.quality_score = result.get("score")
                        st.success("Prompt généré! ✓")
            else:
                st.warning("Veuillez remplir tous les champs")
    
    with col_btn2:
        if st.button("🔧 Optimiser", use_container_width=True):
            if session.generated_prompt:
                with st.spinner("Optimisation en cours..."):
                    result = optimize_prompt(session.generated_prompt)
                    if result:
                        st.info(f"Score initial: {session.quality_score}")
                        if result.get("missing_keywords"):
                            st.warning(f"Mots-clés manquants: {', '.join(result['missing_keywords'])}")
            else:
                st.warning("Générez d'abord un prompt")


# ============================================================================
# Colonne droite: Résultat
# ============================================================================
with col_result:
    st.subheader("📊 Résultat")
    
    if session.generated_prompt:
        # Affichage du prompt
        st.markdown("### Prompt généré")
        st.code(session.generated_prompt, language="text")
        
        # Barre de score
        if session.quality_score is not None:
            st.markdown("### Score de qualité")
            st.progress(session.quality_score / 100)
            st.metric("Score", f"{session.quality_score}/100")
        
        # Bouton pour sauvegarder
        col_save1, col_save2 = st.columns(2)
        with col_save1:
            titre_save = st.text_input("Titre du prompt", value=f"Prompt {task[:20]}")
        with col_save2:
            if st.button("💾 Sauvegarder", use_container_width=True):
                if titre_save:
                    save_prompt_to_db(titre_save, session.generated_prompt, session.quality_score)
    else:
        st.info("👈 Remplissez le formulaire et générez un prompt")


# ============================================================================
# Barre latérale: Historique
# ============================================================================
with st.sidebar:
    st.subheader("📚 Historique")
    st.markdown("Tous les prompts stockés")
    
    prompts = fetch_prompts()
    
    if prompts:
        for idx, prompt in enumerate(prompts):
            with st.expander(
                f"📌 {prompt['titre']} (Score: {prompt['score']}/100)",
                expanded=False
            ):
                st.write(f"**Catégorie:** {prompt['categorie']}")
                st.write(f"**Score:** {prompt['score']}/100")
                st.text_area("Prompt", value=prompt['prompt_text'], height=100, disabled=True)
                
                col_copy, col_del = st.columns(2)
                with col_copy:
                    if st.button("📋 Copier", key=f"copy_{prompt['id']}"):
                        st.write("Prompt copié!")
                
                with col_del:
                    if st.button("🗑️ Supprimer", key=f"delete_{prompt['id']}"):
                        if delete_prompt_from_db(prompt['id']):
                            st.success("Supprimé!")
                            st.rerun()
    else:
        st.info("Aucun prompt sauvegardé")
    
    st.markdown("---")
    st.markdown("*Générateur de Prompts v1.0*")


# ============================================================================
# Footer
# ============================================================================
st.markdown("---")
st.markdown(
    "<div style='text-align: center'><small>Alimenté par FastAPI et Streamlit</small></div>",
    unsafe_allow_html=True
)
"""

frontend_path = frontend_dir / "app.py"
with open(frontend_path, "w", encoding="utf-8") as f:
    f.write(frontend_content)
print(f"✓ Créé: {frontend_path}")

# ============================================================================
# 6. Créer un fichier __init__.py pour le package backend
# ============================================================================
init_path = backend_dir / "__init__.py"
with open(init_path, "w", encoding="utf-8") as f:
    f.write("")
print(f"✓ Créé: {init_path}")

# ============================================================================
# 7. Créer un fichier README.md
# ============================================================================
readme_content = """# Générateur de Prompts

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
"""

readme_path = PROJECT_ROOT / "README.md"
with open(readme_path, "w", encoding="utf-8") as f:
    f.write(readme_content)
print(f"✓ Créé: {readme_path}")

# ============================================================================
# Message final
# ============================================================================
print("\n" + "="*60)
print("✅ PROJET CONFIGURÉ AVEC SUCCÈS!")
print("="*60)
print(f"\nStructure créée dans: {PROJECT_ROOT}\n")
print("Fichiers créés:")
print(f"  ✓ requirements.txt")
print(f"  ✓ backend/__init__.py")
print(f"  ✓ backend/database.py")
print(f"  ✓ backend/optimizer.py")
print(f"  ✓ backend/main.py")
print(f"  ✓ frontend/app.py")
print(f"  ✓ README.md")
print("\n" + "="*60)
print("PROCHAINES ÉTAPES:")
print("="*60)
print("\n1. Installer les dépendances:")
print("   pip install -r requirements.txt\n")
print("2. Démarrer le backend (Terminal 1):")
print("   python backend/main.py\n")
print("3. Démarrer le frontend (Terminal 2):")
print("   streamlit run frontend/app.py\n")
print("="*60)
