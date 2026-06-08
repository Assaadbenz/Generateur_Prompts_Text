# ============================================================================
# OPTIMISATION DE PROMPTS
# ============================================================================
# Ce fichier contient la logique pour analyser et optimiser les prompts IA
# Il calcule un score de qualité et donne des suggestions d'amélioration


def _has_substantial_content(text: str, marker: str) -> bool:
    """Vérifie si une section existe dans le texte et a du contenu substantiel.
    
    Paramètres:
    - text: le texte du prompt à analyser
    - marker: le mot-clé à chercher (ex: "Expert", "Mission")
    
    Retourne: True si la section existe et a plus de 5 caractères
    
    Exemple: _has_substantial_content(prompt, "Expert") vérifie si "Expert" 
    est présent avec du contenu après lui
    """
    # Chercher la position du mot-clé (insensible à la casse)
    idx = text.lower().find(marker.lower())
    if idx == -1:
        # Mot-clé non trouvé
        return False
    # Vérifier qu'il y a du contenu après le mot-clé
    section_start = idx + len(marker)
    # Trouver le prochain retour à la ligne ou fin du texte
    section_end = text.find("\n", section_start) if section_start < len(text) else section_start
    # Extraire le contenu de cette section
    content = text[section_start:section_end].strip()
    # Vérifier qu'il y a au moins 5 caractères de contenu
    return len(content) > 5


def calculate_quality_score(prompt_text: str) -> int:
    """Calcule un score de qualité pour un prompt (0-100).
    
    Le score est basé sur la présence de 4 sections essentielles:
    1. Expert: le rôle de l'IA (25 points)
    2. Mission: l'objectif à accomplir (25 points)
    3. Consignes: les instructions (25 points)
    4. Format: le format de sortie souhaité (25 points)
    
    Total: 100 points pour un prompt parfait
    
    Paramètres:
    - prompt_text: le texte du prompt à analyser
    
    Retourne: score entre 0 et 100
    
    Exemple: Un prompt avec "Expert" et "Mission" aura un score de 50/100
    """
    score = 0
    
    # Vérifier chaque section et ajouter 25 points si elle existe
    if _has_substantial_content(prompt_text, "Expert"):
        score += 25
    if _has_substantial_content(prompt_text, "Mission"):
        score += 25
    if _has_substantial_content(prompt_text, "Consignes"):
        score += 25
    if _has_substantial_content(prompt_text, "Format"):
        score += 25
    
    # S'assurer que le score n'dépasse pas 100
    return min(score, 100)


def optimize_prompt(prompt_text: str) -> dict:
    """Génère des suggestions pour améliorer un prompt.
    
    Cette fonction:
    1. Calcule le score de qualité
    2. Vérifie quelles sections manquent
    3. Donne jusqu'à 2 suggestions pour l'amélioration
    
    Les suggestions suivent l'ordre logique:
    1. RÔLE (Expert) - définir ce que fait l'IA
    2. OBJECTIF (Mission) - expliquer la tâche
    3. ÉTAPES (Consignes) - comment exécuter
    4. FORMAT (Format) - format de réponse souhaité
    
    Paramètres:
    - prompt_text: le prompt à analyser
    
    Retourne: dictionnaire avec:
    - original_prompt: le prompt original
    - optimized_prompt: le prompt (inchangé pour l'instant)
    - score: score de qualité (0-100)
    - missing_keywords: liste des sections manquantes
    - suggestions: liste de suggestions pour améliorer
    """
    # Calculer le score de qualité du prompt
    score = calculate_quality_score(prompt_text)
    missing_keywords = []
    suggestions = []
    
    # Définir les 4 sections essentielles et leurs descriptions
    sections = [
        ("Expert", "Définir le rôle et l'expertise de l'IA"),
        ("Mission", "Expliquer ce qui doit être accompli"),
        ("Consignes", "Fournir les instructions étape par étape"),
        ("Format", "Spécifier le format de sortie souhaité")
    ]
    
    # Vérifier quelles sections manquent
    for section, description in sections:
        if not _has_substantial_content(prompt_text, section):
            missing_keywords.append(section)
    
    # Générer les suggestions en ordre logique et progressif
    if not _has_substantial_content(prompt_text, "Expert"):
        suggestions.append("1️⃣ RÔLE: Ajoute 'Tu es un expert en [domaine]' - Définis d'abord l'expertise")
    
    if not _has_substantial_content(prompt_text, "Mission"):
        suggestions.append("2️⃣ OBJECTIF: Ajoute 'Mission: [description]' - Explique la tâche à accomplir")
    
    if not _has_substantial_content(prompt_text, "Consignes"):
        suggestions.append("3️⃣ ÉTAPES: Ajoute 'Consignes: [instructions]' - Donne les étapes à suivre")
    
    if not _has_substantial_content(prompt_text, "Format"):
        suggestions.append("4️⃣ FORMAT: Ajoute 'Format: [JSON/Liste/Texte]' - Spécifie le format de sortie")
    
    # Si le score est parfait, afficher un message positif
    if score == 100:
        suggestions = ["✅ PARFAIT! Score 100/100 - Votre prompt est complet et pret a utiliser!"]
    else:
        # Limiter à maximum 2 suggestions pour ne pas surcharger l'utilisateur
        suggestions = suggestions[:2]
    
    # Retourner le résultat complet
    return {
        "original_prompt": prompt_text,
        "optimized_prompt": prompt_text,  # Copie du prompt (non modifié pour l'instant)
        "score": score,  # Score de qualité
        "missing_keywords": missing_keywords,  # Sections manquantes
        "suggestions": suggestions  # Suggestions d'amélioration
    }
