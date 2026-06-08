# ============================================================================
# GÉNÉRATEUR DE PROMPTS - BACKEND API
# ============================================================================
# Cette API FastAPI génère et optimise des prompts pour les modèles IA
# Elle fournit des endpoints pour créer, sauvegarder et chercher des prompts

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field  # Pydantic = validation des données
from typing import Dict, Any  # Types pour les annotations
import sys
from pathlib import Path
import os
import json
import io
from dotenv import load_dotenv  # Charger les variables d'environnement du fichier .env

# Charger les variables d'environnement (API_BASE_URL, ALLOWED_ORIGINS, etc.)
load_dotenv()

# Ajouter le répertoire backend au chemin Python pour les imports locaux
sys.path.insert(0, str(Path(__file__).parent))

# Importer les fonctions de gestion de base de données
from database import init_db, save_prompt, get_all_prompts, get_prompt_by_id, delete_prompt, count_prompts, search_prompts, count_search_prompts
# Importer les fonctions d'optimisation de prompts
from optimizer import calculate_quality_score, optimize_prompt

# CORS (Cross-Origin Resource Sharing) permet au frontend (Streamlit) d'accéder à cette API
# Récupérer les origines autorisées depuis les variables d'environnement
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501").split(",")

# ============================================================================
# INITIALISATION DE L'APPLICATION FASTAPI
# ============================================================================
# FastAPI crée automatiquement une documentation interactive à /docs
app = FastAPI(
    title="Générateur de Prompts API",
    description="API pour générer et optimiser des prompts",
    version="1.0.0"
)

# Configuration CORS: autorise les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Domaines autorisés à faire des requêtes
    allow_methods=["*"],             # Tous les méthodes HTTP (GET, POST, etc.)
    allow_headers=["*"],             # Tous les headers HTTP
)

# Créer la table de base de données au démarrage de l'API
init_db()


# ============================================================================
# CONSTANTES ET MODÈLES DE VALIDATION
# ============================================================================
# Les modèles Pydantic valident automatiquement les données reçues de l'API
# Cela évite les erreurs si les données ne sont pas du bon type/format

# Nombre de mots pour chaque longueur de prompt
LENGTH_WORDS = {"Courte": 100, "Moyenne": 300, "Longue": 500}
# Tons possibles pour les prompts
VALID_TONES = ["Très formel", "Formel", "Neutre", "Décontracté", "Très décontracté"]
# Formats de sortie possibles
VALID_FORMATS = ["Texte", "Liste", "Tableau", "Code"]


class PromptRequest(BaseModel):
    """Modèle de validation pour les requêtes de génération de prompts.
    
    Pydantic vérifie automatiquement:
    - expertise: doit avoir entre 1 et 200 caractères
    - mission: doit avoir entre 1 et 2000 caractères
    - tone, output_format, length: doivent être dans les listes VALID_*
    """
    expertise: str = Field(..., min_length=1, max_length=200, description="Domaine d'expertise")
    mission: str = Field(..., min_length=1, max_length=2000, description="Mission à accomplir")
    tone: str = Field(..., description="Ton souhaité")
    output_format: str = Field(default="Texte", description="Format de sortie")
    length: str = Field(default="Moyenne", description="Longueur du prompt")
    
    def validate_inputs(self):
        """Valide que le tone, format et length sont dans les listes autorisées.
        
        Lève une ValueError si l'une des valeurs n'est pas acceptée.
        """
        if self.tone not in VALID_TONES:
            raise ValueError(f"Ton invalide. Valeurs acceptées: {VALID_TONES}")
        if self.output_format not in VALID_FORMATS:
            raise ValueError(f"Format invalide. Valeurs acceptées: {VALID_FORMATS}")
        if self.length not in LENGTH_WORDS:
            raise ValueError(f"Longueur invalide. Valeurs acceptées: {list(LENGTH_WORDS.keys())}")


class PromptResponse(BaseModel):
    titre: str = Field(..., min_length=1)
    prompt_text: str = Field(..., min_length=1)
    score: int = Field(..., ge=0, le=100)


class PromptOptimize(BaseModel):
    prompt_text: str = Field(..., min_length=1)


# ============================================================================
# ENDPOINTS (Routes) DE L'API
# ============================================================================
# Les endpoints sont les "portes" pour accéder à l'API
# @app.get = requête GET (lire des données)
# @app.post = requête POST (créer/modifier des données)

@app.get("/")
async def root():
    """Endpoint racine - simple test pour vérifier que l'API répond."""
    return {"message": "Bienvenue sur l'API Générateur de Prompts"}


@app.get("/health")
async def health_check():
    """Endpoint de vérification de santé - retourne OK si l'API fonctionne.
    
    Utilisé par le frontend pour vérifier que l'API est disponible.
    """
    return {"status": "ok", "message": "API is running"}


@app.post("/generate")
async def generate_prompt(request: PromptRequest) -> Dict[str, Any]:
    """
    Génère un prompt basé sur les paramètres fournis.
    
    Args:
        request.expertise: Domaine d'expertise
        request.mission: Mission à accomplir
        request.tone: Ton souhaité
        request.output_format: Format de sortie
        request.length: Longueur du prompt
    
    Returns:
        Prompt généré avec son score de qualité
    """
    try:
        # Validate input parameters
        request.validate_inputs()
        
        word_count = LENGTH_WORDS.get(request.length, 300)
        prompt_text = f"""Tu es un expert en {request.expertise}.

📋 Mission :
{request.mission}

🎯 Consignes :
- Adopte un ton {request.tone.lower()}
- Réponds au format : {request.output_format}
- Longueur : {request.length} (~{word_count} mots)
- Sois précis, structuré et pertinent
- Adapte ta réponse à la mission confiée

📝 Réponse :"""

        score = calculate_quality_score(prompt_text)
        
        return {
            "titre": f"Prompt - {request.mission[:30]}",
            "prompt_text": prompt_text,
            "score": score
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/optimize")
async def optimize(request: PromptOptimize) -> Dict[str, Any]:
    """
    Optimise un prompt existant.
    
    Args:
        prompt_text: Le prompt à optimiser
    
    Returns:
        Prompt optimisé avec score et recommandations
    """
    try:
        result = optimize_prompt(request.prompt_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/prompts")
async def list_prompts(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    try:
        clamped_limit = min(limit, 100)
        prompts = get_all_prompts(limit=clamped_limit, offset=max(offset, 0))
        total = count_prompts()
        return {"total": total, "limit": clamped_limit, "offset": offset, "prompts": prompts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/prompts/search")
async def search_prompts_route(q: str = "", limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    try:
        if not q or not q.strip():
            return await list_prompts(limit=limit, offset=offset)
        clamped_limit = min(limit, 100)
        prompts = search_prompts(query=q.strip(), limit=clamped_limit, offset=max(offset, 0))
        total = count_search_prompts(query=q.strip())
        return {"total": total, "limit": clamped_limit, "offset": offset, "prompts": prompts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/prompts/{prompt_id}")
async def get_prompt(prompt_id: int) -> Dict[str, Any]:
    """Récupère un prompt spécifique par ID."""
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
    """Sauvegarde un nouveau prompt dans la base de données."""
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
    """Supprime un prompt de la base de données."""
    try:
        success = delete_prompt(prompt_id)
        if not success:
            raise HTTPException(status_code=404, detail="Prompt non trouvé")
        return {"message": "Prompt supprimé avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Export Endpoints
# ============================================================================
@app.get("/export/json")
async def export_json(prompt_id: int = None) -> StreamingResponse:
    """
    Exporte les prompts en JSON.
    
    Args:
        prompt_id: ID d'un prompt spécifique (optionnel). Si vide, exporte tous les prompts.
    
    Returns:
        Fichier JSON téléchargeable
    """
    try:
        if prompt_id:
            # Export d'un prompt spécifique
            prompt = get_prompt_by_id(prompt_id)
            if not prompt:
                raise HTTPException(status_code=404, detail="Prompt non trouvé")
            data = [prompt]
            filename = f"prompt_{prompt_id}.json"
        else:
            # Export de tous les prompts
            data = get_all_prompts(limit=10000, offset=0)
            filename = "prompts_export.json"
        
        # Créer le contenu JSON
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        
        # Retourner comme fichier téléchargeable
        return StreamingResponse(
            io.BytesIO(json_data.encode('utf-8')),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/export/markdown")
async def export_markdown(prompt_id: int = None) -> StreamingResponse:
    """
    Exporte les prompts en Markdown.
    
    Args:
        prompt_id: ID d'un prompt spécifique (optionnel). Si vide, exporte tous les prompts.
    
    Returns:
        Fichier Markdown téléchargeable
    """
    try:
        if prompt_id:
            # Export d'un prompt spécifique
            prompt = get_prompt_by_id(prompt_id)
            if not prompt:
                raise HTTPException(status_code=404, detail="Prompt non trouvé")
            data = [prompt]
            filename = f"prompt_{prompt_id}.md"
        else:
            # Export de tous les prompts
            data = get_all_prompts(limit=10000, offset=0)
            filename = "prompts_export.md"
        
        # Créer le contenu Markdown
        markdown_content = "# Prompts Export\n\n"
        markdown_content += f"📅 Export Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        markdown_content += f"📊 Total Prompts: {len(data)}\n\n"
        markdown_content += "---\n\n"
        
        for i, prompt in enumerate(data, 1):
            markdown_content += f"## {i}. {prompt.get('titre', 'Sans titre')}\n\n"
            markdown_content += f"**ID:** {prompt.get('id')}\n\n"
            markdown_content += f"**Catégorie:** {prompt.get('categorie', 'N/A')}\n\n"
            markdown_content += f"**Score:** {prompt.get('score', 'N/A')}/100\n\n"
            markdown_content += f"**Date:** {prompt.get('date_creation', 'N/A')}\n\n"
            markdown_content += "### Contenu du Prompt\n\n"
            markdown_content += f"```\n{prompt.get('prompt_text', 'N/A')}\n```\n\n"
            markdown_content += "---\n\n"
        
        # Retourner comme fichier téléchargeable
        return StreamingResponse(
            io.BytesIO(markdown_content.encode('utf-8')),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
