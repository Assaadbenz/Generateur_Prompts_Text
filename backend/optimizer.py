def _has_substantial_content(text: str, marker: str) -> bool:
    """Verifie si une section existe et a du contenu substantiel."""
    idx = text.lower().find(marker.lower())
    if idx == -1:
        return False
    # Verifier qu'il y a plus que juste le marqueur
    section_start = idx + len(marker)
    section_end = text.find("\n", section_start) if section_start < len(text) else section_start
    content = text[section_start:section_end].strip()
    return len(content) > 5  # Au moins 5 caracteres


def calculate_quality_score(prompt_text: str) -> int:
    """
    Calcule un score de qualité (0-100).
    25 points par section substantielle (Expert, Mission, Consignes, Format) = 100pts
    """
    score = 0
    
    # 25 points par section presente ET substantielle
    if _has_substantial_content(prompt_text, "Expert"):
        score += 25
    if _has_substantial_content(prompt_text, "Mission"):
        score += 25
    if _has_substantial_content(prompt_text, "Consignes"):
        score += 25
    if _has_substantial_content(prompt_text, "Format"):
        score += 25
    
    return min(score, 100)


def optimize_prompt(prompt_text: str) -> dict:
    """
    Genere des suggestions logiques et progressives pour ameliorer le prompt.
    Ordre logique: 1) Role (Expert) 2) But (Mission) 3) Instructions (Consignes) 4) Sortie (Format)
    """
    score = calculate_quality_score(prompt_text)
    missing_keywords = []
    suggestions = []
    
    # Verifications dans l'ordre logique
    sections = [
        ("Expert", "Define the AI's role and expertise"),
        ("Mission", "Explain what needs to be accomplished"),
        ("Consignes", "Provide step-by-step instructions"),
        ("Format", "Specify the output format needed")
    ]
    
    for section, description in sections:
        if not _has_substantial_content(prompt_text, section):
            missing_keywords.append(section)
    
    # Generer les suggestions en ordre logique et progressive
    if not _has_substantial_content(prompt_text, "Expert"):
        suggestions.append("1️⃣ RÔLE: Ajoute 'Tu es un expert en [domaine]' - Définis d'abord l'expertise")
    
    if not _has_substantial_content(prompt_text, "Mission"):
        suggestions.append("2️⃣ OBJECTIF: Ajoute 'Mission: [description]' - Explique la tâche à accomplir")
    
    if not _has_substantial_content(prompt_text, "Consignes"):
        suggestions.append("3️⃣ ÉTAPES: Ajoute 'Consignes: [instructions]' - Donne les étapes à suivre")
    
    if not _has_substantial_content(prompt_text, "Format"):
        suggestions.append("4️⃣ FORMAT: Ajoute 'Format: [JSON/Liste/Texte]' - Spécifie le format de sortie")
    
    # Perfect score feedback
    if score == 100:
        suggestions = ["✅ PARFAIT! Score 100/100 - Votre prompt est complet et pret a utiliser!"]
    else:
        # Max 2 suggestions at a time (focus on what matters most)
        suggestions = suggestions[:2]
    
    return {
        "original_prompt": prompt_text,
        "optimized_prompt": prompt_text,
        "score": score,
        "missing_keywords": missing_keywords,
        "suggestions": suggestions
    }
