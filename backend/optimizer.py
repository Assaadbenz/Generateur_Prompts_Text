# ============================================================================
# OPTIMISATION DE PROMPTS - SCORING 3 CRITÈRES
# ============================================================================
# Score final (0-100) basé sur 3 dimensions :
#
#   1. STRUCTURE   (40 pts) – sections clés présentes (rôle, mission, consignes, format)
#   2. LONGUEUR    (25 pts) – taille équilibrée (zone idéale : 40-250 mots)
#   3. SPÉCIFICITÉ (35 pts) – chiffres, exemples, contraintes, public cible

import re
from typing import Dict, Any, List, Tuple


# ============================================================================
# CONSTANTES
# ============================================================================

# Sections structurelles attendues dans un bon prompt
SECTIONS = {
    "Rôle":      ["tu es", "vous êtes", "agis comme", "act as", "expert en", "spécialiste"],
    "Mission":   ["mission", "objectif", "tâche", "but :", "ta mission"],
    "Consignes": ["consigne", "instruction", "étape", "règle", "contrainte"],
    "Format":    ["format", "réponds", "liste", "tableau", "json", "code", "texte"],
}

# Marqueurs de spécificité
SPECIFICITY_PATTERNS = {
    "Chiffres":    r"\b\d+\s*(?:mots?|lignes?|étapes?|exemples?|points?|%|€|\$)?\b",
    "Exemples":    r"\b(?:par exemple|e\.g\.|comme|tel que|notamment)\b",
    "Contraintes": r"\b(?:uniquement|seulement|jamais|toujours|obligatoire|interdit|maximum|minimum|au moins)\b",
    "Public":      r"\b(?:pour|destiné à|audience|cible|débutant|expert|professionnel|utilisateur)\b",
}

# Plages de longueur (en mots)
LENGTH_IDEAL_MIN = 40
LENGTH_IDEAL_MAX = 250


# ============================================================================
# FONCTIONS PRIVÉES
# ============================================================================

def _has_section(text: str, keywords: List[str]) -> bool:
    """Vérifie qu'un mot-clé est présent ET suivi d'au moins 8 caractères."""
    text_lower = text.lower()
    for kw in keywords:
        idx = text_lower.find(kw.lower())
        if idx != -1 and len(text[idx + len(kw):idx + len(kw) + 60].strip()) >= 8:
            return True
    return False


def _score_structure(text: str) -> Tuple[int, List[str]]:
    """40 pts — 10 pts par section présente (Rôle, Mission, Consignes, Format)."""
    feedbacks = []
    score = 0
    for name, keywords in SECTIONS.items():
        if _has_section(text, keywords):
            score += 10
        else:
            tips = {
                "Rôle":      "Ajoute 'Tu es un expert en [domaine]'",
                "Mission":   "Ajoute 'Mission : [description de la tâche]'",
                "Consignes": "Ajoute 'Consignes :' avec des règles numérotées",
                "Format":    "Précise 'Format : [Liste/Texte/JSON/Code]'",
            }
            feedbacks.append(f"📌 {name.upper()} manquant — {tips[name]}")
    return score, feedbacks


def _score_longueur(text: str) -> Tuple[int, List[str]]:
    """25 pts — zone idéale 40-250 mots, pénalité progressive hors zone."""
    feedbacks = []
    n = len(text.split())

    if n < 20:
        score, msg = 0, f"📏 TROP COURT ({n} mots) — Vise au moins {LENGTH_IDEAL_MIN} mots."
    elif n < LENGTH_IDEAL_MIN:
        score, msg = 8, f"📏 COURT ({n} mots) — Développe les consignes pour atteindre {LENGTH_IDEAL_MIN}+ mots."
    elif n <= LENGTH_IDEAL_MAX:
        return 25, []
    elif n <= 400:
        score, msg = 14, f"📏 UN PEU LONG ({n} mots) — Condense les instructions redondantes."
    else:
        score, msg = 5, f"📏 TROP LONG ({n} mots) — Supprime les répétitions (idéal < 250 mots)."

    feedbacks.append(msg)
    return score, feedbacks


def _score_specificite(text: str) -> Tuple[int, List[str]]:
    """35 pts — ~9 pts par marqueur présent (Chiffres, Exemples, Contraintes, Public)."""
    feedbacks = []
    score = 0
    pts = 35 // len(SPECIFICITY_PATTERNS)  # ~8 pts chacun (arrondi)

    tips = {
        "Chiffres":    "🔢 Ajoute des chiffres concrets : 'en 5 étapes', '200 mots max', '3 exemples'.",
        "Exemples":    "💡 Inclure 'par exemple…' aide l'IA à calibrer le style attendu.",
        "Contraintes": "🚫 Précise ce que l'IA ne doit PAS faire : 'uniquement des faits', 'sans introduction'.",
        "Public":      "👥 Indique le public : 'pour des débutants', 'à destination de managers'.",
    }

    for name, pattern in SPECIFICITY_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            score += pts
        else:
            feedbacks.append(tips[name])

    return min(score, 35), feedbacks


# ============================================================================
# API PUBLIQUE
# ============================================================================

def calculate_quality_score(prompt_text: str) -> int:
    """
    Calcule un score de qualité pour un prompt (0-100).

    3 dimensions :
    - Structure   : 40 pts (4 sections × 10 pts)
    - Longueur    : 25 pts (zone idéale 40-250 mots)
    - Spécificité : 35 pts (4 marqueurs × ~9 pts)

    Retourne: score entier entre 0 et 100
    """
    if not prompt_text or not prompt_text.strip():
        return 0
    s, _ = _score_structure(prompt_text)
    l, _ = _score_longueur(prompt_text)
    sp, _ = _score_specificite(prompt_text)
    return min(s + l + sp, 100)


def get_score_breakdown(prompt_text: str) -> Dict[str, Any]:
    """Retourne le détail du score par dimension."""
    if not prompt_text or not prompt_text.strip():
        return {"total": 0, "breakdown": {}, "all_feedbacks": ["⚠️ Le prompt est vide."]}

    s,  fb_s  = _score_structure(prompt_text)
    l,  fb_l  = _score_longueur(prompt_text)
    sp, fb_sp = _score_specificite(prompt_text)

    total = min(s + l + sp, 100)

    breakdown = {
        "Structure":   {"score": s,  "max": 40, "pct": int(s  / 40  * 100)},
        "Longueur":    {"score": l,  "max": 25, "pct": int(l  / 25  * 100)},
        "Spécificité": {"score": sp, "max": 35, "pct": int(sp / 35  * 100)},
    }

    return {
        "total":        total,
        "breakdown":    breakdown,
        "all_feedbacks": fb_s + fb_l + fb_sp,
    }


def optimize_prompt(prompt_text: str) -> dict:
    """
    Analyse un prompt et retourne un diagnostic avec suggestions (max 3).

    Retourne:
    - original_prompt  : prompt original
    - optimized_prompt : idem (réécriture auto prévue v2)
    - score            : score global (0-100)
    - breakdown        : détail par dimension
    - missing_keywords : dimensions en dessous de 50%
    - suggestions      : jusqu'à 3 conseils prioritaires
    """
    details = get_score_breakdown(prompt_text)
    score      = details["total"]
    breakdown  = details["breakdown"]
    feedbacks  = details["all_feedbacks"]

    missing_keywords = [
        dim for dim, v in breakdown.items() if v["pct"] < 50
    ]

    if score >= 85:
        suggestions = [f"✅ Excellent ({score}/100) — Votre prompt est prêt à l'emploi !"]
    else:
        suggestions = feedbacks[:3]

    return {
        "original_prompt":  prompt_text,
        "optimized_prompt": prompt_text,
        "score":            score,
        "breakdown":        breakdown,
        "missing_keywords": missing_keywords,
        "suggestions":      suggestions,
    }
