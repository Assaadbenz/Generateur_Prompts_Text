def _extract_section(text: str, marker: str, after: str = "") -> str:
    """Extrait le contenu d'une section du prompt."""
    idx = text.lower().find(marker.lower())
    if idx == -1:
        return ""
    start = idx + len(marker)
    if after:
        aidx = text.lower().find(after.lower(), start)
        if aidx != -1:
            start = aidx + len(after)
    # Prendre jusqu'à la prochaine ligne vide ou fin
    end = text.find("\n\n", start)
    if end == -1:
        end = len(text)
    return text[start:end].strip()


def calculate_quality_score(prompt_text: str) -> int:
    """
    Calcule un score de qualité (0-100).
    
    - Sections présentes (expert, mission, consignes, format): 8pts chacune = 32
    - Profondeur de la mission (selon longueur du texte): 0-25
    - Spécificité de l'expertise: 0-15
    - Format de sortie mentionné: 8
    - Longueur mentionnée: 8
    - Qualité globale du prompt: 0-12
    """
    lower = prompt_text.lower()
    
    sections = ["expert", "mission", "consignes", "format"]
    score = sum(8 for s in sections if s in lower)
    
    mission_text = _extract_section(prompt_text, "Mission :")
    if mission_text:
        ml = len(mission_text)
        if ml > 200:
            score += 25
        elif ml > 100:
            score += 20
        elif ml > 50:
            score += 15
        elif ml > 20:
            score += 8
        else:
            score += 3
    
    expert_text = _extract_section(prompt_text, "Tu es un expert en", "en ")
    if expert_text:
        el = len(expert_text)
        if el > 30:
            score += 15
        elif el > 15:
            score += 10
        elif el > 5:
            score += 5
    
    if "format :" in lower:
        score += 8
    if "longueur :" in lower:
        score += 8
    
    if len(prompt_text) > 300:
        score += 12
    elif len(prompt_text) > 150:
        score += 6
    
    return min(score, 100)


def optimize_prompt(prompt_text: str) -> dict:
    score = calculate_quality_score(prompt_text)
    optimized = prompt_text
    missing_keywords = []
    suggestions = []
    
    checks = {"Expert": "expert", "Mission": "mission", "Consignes": "consignes", "Format": "format"}
    for label, keyword in checks.items():
        if keyword not in prompt_text.lower():
            missing_keywords.append(label)
            suggestions.append(f"Ajoutez une section **{label}** : décrivez le {label.lower()} attendu")
    
    mission_text = _extract_section(prompt_text, "Mission :")
    if mission_text and len(mission_text) < 50:
        suggestions.append("**Mission** trop courte : détaillez davantage la tâche à accomplir (+50 caractères)")
    
    expert_text = _extract_section(prompt_text, "Tu es un expert en", "en ")
    if expert_text and len(expert_text) < 15:
        suggestions.append("**Mission** : manque de mots-clés, soyez plus précis dans la description")
    elif mission_text and len(expert_text) >= 15 and len(mission_text) < 50:
        suggestions.append("**Mission** : manque de mots-clés, soyez plus précis dans la description")
    
    if not suggestions:
        suggestions.append("Le prompt est bien structuré et complet")
    
    return {
        "original_prompt": prompt_text,
        "optimized_prompt": optimized,
        "score": score,
        "missing_keywords": missing_keywords,
        "suggestions": suggestions
    }
