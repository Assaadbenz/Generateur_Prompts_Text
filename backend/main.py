from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ajouter le répertoire backend au path
sys.path.insert(0, str(Path(__file__).parent))

from database import init_db, save_prompt, get_all_prompts, get_prompt_by_id, delete_prompt, count_prompts, search_prompts, count_search_prompts
from optimizer import calculate_quality_score, optimize_prompt

# Get CORS origins from environment or use defaults
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501").split(",")

# Initialiser l'app FastAPI
app = FastAPI(
    title="Générateur de Prompts API",
    description="API pour générer et optimiser des prompts",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialiser la base de données au démarrage
init_db()


# ============================================================================
# Modèles Pydantic
# ============================================================================
LENGTH_WORDS = {"Courte": 100, "Moyenne": 300, "Longue": 500}
VALID_TONES = ["Très formel", "Formel", "Neutre", "Décontracté", "Très décontracté"]
VALID_FORMATS = ["Texte", "Liste", "Tableau", "Code"]


class PromptRequest(BaseModel):
    expertise: str = Field(..., min_length=1, max_length=200, description="Domaine d'expertise")
    mission: str = Field(..., min_length=1, max_length=2000, description="Mission à accomplir")
    tone: str = Field(..., description="Ton souhaité")
    output_format: str = Field(default="Texte", description="Format de sortie")
    length: str = Field(default="Moyenne", description="Longueur du prompt")
    
    def validate_inputs(self):
        """Validate tone and format against allowed values."""
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
# Routes
# ============================================================================
@app.get("/")
async def root():
    """Endpoint racine pour tester l'API."""
    return {"message": "Bienvenue sur l'API Générateur de Prompts"}


@app.get("/health")
async def health_check():
    """Health check endpoint to verify API is running."""
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
