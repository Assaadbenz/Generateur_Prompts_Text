def calculate_quality_score(prompt_text: str) -> int:
    """
    Calcule un score de qualité (0-100) basé sur les mots-clés présents.
    
    Mots-clés recherchés: "expert", "mission", "consignes", "format"
    - Chaque mot-clé présent ajoute 20 points
    - Bonus longueur (> 50 caractères): +10 points
    - Bonus complétude (4/4 mots-clés): +10 points
    
    Args:
        prompt_text: Le texte du prompt à évaluer
    
    Returns:
        Score entre 0 et 100
    """
    keywords = ["expert", "mission", "consignes", "format"]
    prompt_lower = prompt_text.lower()
    
    score = 0
    found = 0
    for keyword in keywords:
        if keyword in prompt_lower:
            score += 20
            found += 1
    
    # Bonus pour la longueur
    if len(prompt_text) > 50:
        score += 10
    
    # Bonus si tous les mots-clés sont présents
    if found == len(keywords):
        score += 10
    
    return min(score, 100)


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
    
    checks = {"Expert": "expert", "Mission": "mission", "Consignes": "consignes", "Format": "format"}
    for label, keyword in checks.items():
        if keyword not in prompt_text.lower():
            missing_keywords.append(label)
    
    return {
        "original_prompt": prompt_text,
        "optimized_prompt": optimized,
        "score": score,
        "missing_keywords": missing_keywords
    }
