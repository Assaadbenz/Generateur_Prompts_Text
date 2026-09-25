"""
Service de génération et d'optimisation de prompts utilisant l'API Google Gemini.
Prend en charge gemini-1.5-flash et gemini-2.5-flash.
"""

import os
import json
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


def get_gemini_api_key(override_key: Optional[str] = None) -> Optional[str]:
    """Récupère la clé API Gemini depuis le paramètre d'appel ou les variables d'environnement."""
    if override_key and override_key.strip():
        return override_key.strip()
    key = os.getenv("GEMINI_API_KEY", "").strip()
    return key if key else None


def call_gemini_api(prompt_instruction: str, api_key: Optional[str] = None, model: Optional[str] = None) -> str:
    """Appelle l'API REST de Google Gemini avec bascule automatique de modèle en cas de pic de charge."""
    key = get_gemini_api_key(api_key)
    if not key:
        raise ValueError(
            "Clé API Google Gemini manquante. Veuillez définir GEMINI_API_KEY dans votre fichier .env "
            "ou la saisir dans l'interface."
        )

    # Ordre des modèles à essayer (pour parer aux pics de charge 503)
    configured_model = model or os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    candidate_models = [configured_model, "gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.8-flash"]
    # Dédupliquer tout en préservant l'ordre
    seen = set()
    models_to_try = [m for m in candidate_models if not (m in seen or seen.add(m))]

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_instruction}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048,
        }
    }

    last_error = None
    for candidate in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{candidate}:generateContent?key={key}"
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=25)
            if response.status_code == 200:
                data = response.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    return "".join(part.get("text", "") for part in parts).strip()
            elif response.status_code in (503, 404):
                # Réessayer avec le modèle suivant en cas de surcharge temporaire
                last_error = f"Model {candidate} returned {response.status_code}"
                continue
            else:
                error_msg = response.text
                try:
                    err_json = response.json()
                    error_msg = err_json.get("error", {}).get("message", response.text)
                except Exception:
                    pass
                raise RuntimeError(f"Erreur API Gemini ({response.status_code}): {error_msg}")
        except requests.exceptions.RequestException as e:
            last_error = str(e)
            continue

    raise RuntimeError(f"Erreur API Gemini : Tous les modèles sont temporairement indisponibles ({last_error})")


def generate_prompt_ai(
    expertise: str,
    mission: str,
    tone: str,
    output_format: str,
    length: str,
    api_key: Optional[str] = None
) -> str:
    """Génère un prompt professionnel complet en utilisant l'API Google Gemini."""
    key = get_gemini_api_key(api_key)

    instruction = f"""Tu es un expert d'élite en Prompt Engineering pour les modèles de langage (LLM).
Ton objectif est de créer un prompt puissant, structuré et hautement efficace pour un modèle d'IA.

Voici les exigences de l'utilisateur :
- Domaine d'expertise : {expertise}
- Mission à accomplir : {mission}
- Tonalité : {tone}
- Format attendu : {output_format}
- Longueur visée : {length}

Directives pour le prompt généré :
1. Attribue un rôle clair, précis et qualifié (Persona d'expert).
2. Définis le contexte et l'objectif exact de la mission.
3. Rédige des consignes et règles opérationnelles structurées (numérotées ou à puces).
4. Spécifie des contraintes négatives (ce que l'IA ne doit PAS faire).
5. Explicite le format de restitution attendu ({output_format}).
6. N'ajoute AUCUN texte explicatif ni préambule avant ou après le prompt (pas de "Voici votre prompt :").
7. Rends le prompt directement copiable et immédiatement opérationnel."""

    if key:
        return call_gemini_api(instruction, api_key=key)
    else:
        # Si aucune clé n'est encore configurée, simuler une génération intelligente
        word_count = {"Courte": 100, "Moyenne": 300, "Longue": 500}.get(length, 300)
        return f"""# PROMPT EXPERT : {expertise.upper()}

Tu es un expert reconnu en {expertise}, spécialisé dans la résolution de problématiques complexes.

## 🎯 Contexte & Mission
{mission}

## 📋 Directives Opérationnelles
1. Adopte rigoureusement une tonalité {tone.lower()}.
2. Fournis une analyse détaillée, structurée et directement applicable.
3. Inclus au moins 3 exemples concrets ou recommandations pratiques.
4. Contrainte : Évite toute généralité ou formule d'introduction inutile.

## 📤 Format de Sortie Attendu
- Réponds au format : {output_format}
- Envergure visée : environ {word_count} mots
- Utilise des sous-titres clairs et une mise en page soignée."""


def optimize_prompt_ai(prompt_text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Optimise et réécrit un prompt existant en utilisant l'API Google Gemini."""
    key = get_gemini_api_key(api_key)

    if not key:
        # Fallback si pas de clé : enrichissement intelligent
        optimized = f"""Tu es un expert qualifié et méthodique.

## Contexte & Objectif
{prompt_text}

## Directives d'exécution
1. Développe ta réponse avec précision et clarté.
2. Structure la réflexion en points numérotés et ajoute des exemples réels.
3. Ne commence pas par des formules de politesse superflues.

## Format
Présente une synthèse opérationnelle avec puces et étapes d'action."""
        return {
            "optimized_prompt": optimized,
            "suggestions": [
                "Structure renforcée avec ajout de sections claires.",
                "Ajout de contraintes négatives pour supprimer les banalités.",
                "Précision du rôle et du contexte de sortie."
            ]
        }

    instruction = f"""Tu es un auditeur et optimiseur expert de prompts IA.
Voici un prompt rédigé par un utilisateur :
```
{prompt_text}
```

Ta mission :
1. Réécris ce prompt pour le rendre de niveau professionnel (ajoute un Persona expert précis, des contraintes d'exécution, des consignes structurées, des exemples de format et des contraintes négatives).
2. Fournis 3 suggestions d'amélioration clés.

Réponds UNIQUEMENT sous la forme d'un objet JSON strict valide sans texte avant ni après, avec ce format :
{{
  "optimized_prompt": "Le prompt intégralement réécrit et enrichi",
  "suggestions": [
    "Suggestion 1",
    "Suggestion 2",
    "Suggestion 3"
  ]
}}"""

    raw_response = call_gemini_api(instruction, api_key=key)

    try:
        # Nettoyage Markdown JSON si présent
        cleaned = raw_response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        data = json.loads(cleaned.strip())
        return {
            "optimized_prompt": data.get("optimized_prompt", prompt_text),
            "suggestions": data.get("suggestions", ["Prompt restructuré par Google Gemini."])
        }
    except Exception:
        return {
            "optimized_prompt": raw_response,
            "suggestions": ["Prompt réécrit et optimisé par l'IA Google Gemini."]
        }
