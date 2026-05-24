import requests
from typing import Optional


def calculate_quality_score(prompt_text: str) -> int:
    """
    Calcule un score de qualité (0-100) basé sur les mots-clés présents.
    
    Mots-clés recherchés: "Rôle", "Contexte", "Format"
    - Chaque mot-clé présent ajoute 30 points
    - Longueur du prompt: +10 points si > 50 caractères
    
    Args:
        prompt_text: Le texte du prompt à évaluer
    
    Returns:
        Score entre 0 et 100
    """
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
    """
    Appelle l'API Hugging Face pour générer/améliorer un prompt.
    
    Args:
        prompt_text: Le prompt initial
        api_key: Clé API Hugging Face (optionnelle, à mettre en variable d'env)
    
    Returns:
        Dictionnaire avec la réponse de l'API
    """
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
    """
    Optimise un prompt en calculant son score et en proposant des améliorations.
    
    Args:
        prompt_text: Le prompt à optimiser
    
    Returns:
        Dictionnaire avec le score et le prompt optimisé
    """
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
