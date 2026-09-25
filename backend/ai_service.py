"""
Service d'orchestration d'IA multi-fournisseurs (LLM).
Prend en charge :
- Google Gemini (REST API)
- OpenAI (GPT-4o, GPT-4o-mini)
- Groq (Llama 3.3 70B, Llama 3.1 8B)
- Ollama (LLMs locaux)
- Mock / Mode Démo intelligent (pour tests, CI et exécution hors ligne sans clé)

Intègre les frameworks reconnus de Prompt Engineering (RTF, CRISPE, Few-Shot, Chain-of-Thought).
"""

import time
import json
import httpx
from typing import Dict, Any, Optional, Tuple, List
from backend.config import settings
from backend.logger import logger


class AIService:
    """Service d'orchestration pour la génération et l'optimisation de prompts par IA."""

    FRAMEWORKS = {
        "RTF": "Role-Task-Format (Classique & Efficace)",
        "CRISPE": "Capacity, Role, Insight, Statement, Personality, Experiment",
        "FEW_SHOT": "Few-Shot (Avec exemples concrets d'entrée/sortie)",
        "CHAIN_OF_THOUGHT": "Chain-of-Thought (Raisonnement étape par étape)",
        "SYSTEM_DIRECTIVE": "Production System Prompt (Directives strictes & balises XML)",
    }

    TARGET_MODELS = [
        "Universel (Tous LLMs)",
        "ChatGPT / OpenAI (GPT-4o)",
        "Claude (Anthropic)",
        "Google Gemini",
        "Open-Source (Llama 3 / Mistral)",
    ]

    def __init__(self):
        self.timeout = settings.AI_TIMEOUT_SECONDS

    def get_available_providers(self) -> Dict[str, Any]:
        """Retourne l'état de disponibilité des fournisseurs configurés."""
        return {
            "gemini": {
                "available": bool(settings.GEMINI_API_KEY),
                "model": settings.GEMINI_MODEL,
                "label": "Google Gemini (Gemini 1.5/2.5 Flash)",
            },
            "openai": {
                "available": bool(settings.OPENAI_API_KEY),
                "model": settings.OPENAI_MODEL,
                "label": "OpenAI (GPT-4o-mini / GPT-4o)",
            },
            "groq": {
                "available": bool(settings.GROQ_API_KEY),
                "model": settings.GROQ_MODEL,
                "label": "Groq Cloud (Llama 3.3 70B - Ultra Rapide)",
            },
            "ollama": {
                "available": True,
                "model": settings.OLLAMA_MODEL,
                "label": f"Ollama Local ({settings.OLLAMA_MODEL})",
            },
            "mock": {
                "available": True,
                "model": "deterministic-v2",
                "label": "Mode Démo / Mock IA (Aucune clé requise)",
            },
        }

    def resolve_provider(self, requested_provider: Optional[str] = None, api_key: Optional[str] = None) -> str:
        """Détermine le fournisseur d'IA à utiliser en fonction de la configuration et des clés disponibles."""
        if requested_provider and requested_provider in ("gemini", "openai", "groq", "ollama", "mock"):
            if requested_provider == "gemini" and not (api_key or settings.GEMINI_API_KEY):
                logger.warning("Gemini demandé sans clé API, bascule sur mock.")
                return "mock"
            if requested_provider == "openai" and not (api_key or settings.OPENAI_API_KEY):
                logger.warning("OpenAI demandé sans clé API, bascule sur mock.")
                return "mock"
            if requested_provider == "groq" and not (api_key or settings.GROQ_API_KEY):
                logger.warning("Groq demandé sans clé API, bascule sur mock.")
                return "mock"
            return requested_provider

        # Auto-détection par ordre de priorité si configuré
        if settings.GEMINI_API_KEY:
            return "gemini"
        if settings.GROQ_API_KEY:
            return "groq"
        if settings.OPENAI_API_KEY:
            return "openai"

        return "mock"

    async def _call_gemini(
        self,
        system_instruction: str,
        user_message: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """Appel à l'API Google Gemini via REST."""
        key = api_key or settings.GEMINI_API_KEY
        if not key:
            raise ValueError("Clé GEMINI_API_KEY manquante.")

        selected_model = model or settings.GEMINI_MODEL
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent?key={key}"

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{system_instruction}\n\n{user_message}"}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 2048,
            }
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                logger.error(f"Erreur Gemini API ({response.status_code}): {response.text}")
                raise RuntimeError(f"Erreur API Gemini ({response.status_code}): {response.text}")
            
            data = response.json()
            try:
                candidates = data.get("candidates", [])
                if not candidates:
                    raise RuntimeError("Réponse Gemini vide.")
                parts = candidates[0].get("content", {}).get("parts", [])
                return "".join(part.get("text", "") for part in parts).strip()
            except Exception as e:
                logger.error(f"Erreur parsing Gemini: {e}")
                raise RuntimeError(f"Format de réponse Gemini inattendu : {e}")

    async def _call_openai_compatible(
        self,
        endpoint: str,
        api_key: Optional[str],
        model: str,
        system_instruction: str,
        user_message: str,
        temperature: float = 0.7,
    ) -> str:
        """Appel générique pour endpoints compatibles OpenAI (OpenAI, Groq, Ollama)."""
        headers = {
            "Content-Type": "application/json",
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_message},
            ],
            "temperature": temperature,
            "max_tokens": 2048,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(endpoint, headers=headers, json=payload)
            if response.status_code != 200:
                logger.error(f"Erreur API ({response.status_code}): {response.text}")
                raise RuntimeError(f"Erreur API ({response.status_code}): {response.text}")

            data = response.json()
            try:
                return data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                logger.error(f"Erreur parsing réponse compatible OpenAI: {e}")
                raise RuntimeError(f"Format de réponse inattendu : {e}")

    async def _dispatch_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        provider: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Tuple[str, str, float]:
        """
        Envoie la requête au fournisseur LLM adéquat.
        Retourne : (texte_généré, modèle_utilisé, latence_secondes)
        """
        start_time = time.time()
        active_provider = self.resolve_provider(provider, api_key)
        
        logger.info(f"Appel LLM via provider={active_provider} | model={model}")

        if active_provider == "gemini":
            selected_model = model or settings.GEMINI_MODEL
            text = await self._call_gemini(system_prompt, user_prompt, selected_model, api_key, temperature)
            used_model = f"Gemini ({selected_model})"

        elif active_provider == "openai":
            selected_model = model or settings.OPENAI_MODEL
            key = api_key or settings.OPENAI_API_KEY
            text = await self._call_openai_compatible(
                "https://api.openai.com/v1/chat/completions",
                key,
                selected_model,
                system_prompt,
                user_prompt,
                temperature,
            )
            used_model = f"OpenAI ({selected_model})"

        elif active_provider == "groq":
            selected_model = model or settings.GROQ_MODEL
            key = api_key or settings.GROQ_API_KEY
            text = await self._call_openai_compatible(
                "https://api.groq.com/openai/v1/chat/completions",
                key,
                selected_model,
                system_prompt,
                user_prompt,
                temperature,
            )
            used_model = f"Groq ({selected_model})"

        elif active_provider == "ollama":
            selected_model = model or settings.OLLAMA_MODEL
            endpoint = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/chat/completions"
            text = await self._call_openai_compatible(
                endpoint,
                None,
                selected_model,
                system_prompt,
                user_prompt,
                temperature,
            )
            used_model = f"Ollama ({selected_model})"

        else:
            # Mode MOCK / Démo
            await httpx.AsyncClient().get("http://localhost:8000/health", timeout=0.05).catch(lambda _: None) if False else None
            # Simuler un court délai de réponse d'un LLM rapide
            time.sleep(0.3)
            text = self._generate_intelligent_mock(system_prompt, user_prompt)
            used_model = "AI Generator (Demo Engine - Sans Clé)"

        latency = round(time.time() - start_time, 2)
        return text, used_model, latency

    def _generate_intelligent_mock(self, system_prompt: str, user_prompt: str) -> str:
        """Génère une réponse structurée de haute qualité lorsque aucune clé API n'est fournie."""
        # Si c'est une demande d'optimisation
        if "optimis" in system_prompt.lower() or "audit" in system_prompt.lower():
            return """# 🎯 PROMPT OPTIMISÉ (Architecture de Production)

Tu es un expert chevronné et un conseiller stratégique spécialisé dans ce domaine.

## 📋 Contexte & Objectif
Ta mission consiste à analyser rigoureusement la demande, identifier les facteurs critiques de succès et formuler une réponse à forte valeur ajoutée.

## ⚙️ Directives & Règles d'Exécution
1. **Précision & Clarté** : Évite les banalités et le remplissage. Fournis des explications précises, argumentées et directement actionnables.
2. **Méthodologie Étape par Étape** : Décompose les concepts complexes en phases logiques et ordonnées.
3. **Exemples Concrets** : Illustre chaque recommandation clé par au moins 2 cas d'usage réels ou métriques chiffrées.
4. **Contraintes Négatives** : Ne commence pas par des formules de politesse superflues (ex: "Bien sûr, je vais..."). Va droit au but.

## 📊 Format de Restitution
- **Section 1** : Synthèse exécutive & Diagnostic rapide
- **Section 2** : Plan d'action détaillé en 5 étapes clés avec responsabilités
- **Section 3** : Matrice des risques et solutions préventives
- **Section 4** : Checklist finale de validation"""

        # Si c'est un test bac à sable
        if "bac à sable" in system_prompt.lower() or "test de prompt" in system_prompt.lower():
            return """[RÉPONSE DU MODÈLE IA AU PROMPT TESTÉ]

✅ Analyse effectuée avec succès.
Voici la démonstration concrète de l'application de votre prompt :
1. Les contraintes de rôle et de ton ont été scrupuleusement respectées.
2. Le formatage demandé est appliqué avec structure et concision.
3. Les données clés et points d'action sont mis en exergue pour une lecture instantanée."""

        # Cas général de génération de prompt
        return f"""# 🚀 PROMPT SYSTÈME OPTIMISÉ POUR LLM

Tu agis en tant qu'expert de haut niveau doté d'une expérience reconnue dans la discipline requise.

## 🎯 Rôle & Posture
- Incarne une autorité reconnue dans le domaine, rigoureuse, pédagogue et orientée résultats.
- Maintiens un esprit critique constructif et privilégie les solutions éprouvées.

## 📌 Mission Principale
{user_prompt}

## 📋 Spécifications & Contraintes Opérationnelles
- **Structure** : Rédige une réponse limpide, scindée en sections titrées et aérées.
- **Rigueur** : Étaye tes propos avec des méthodologies éprouvées (chiffres, frameworks, bonnes pratiques).
- **Style** : Professionnel, percutant, exempt de jargon non expliqué.
- **Exhaustivité ciblée** : Fournis toutes les informations nécessaires sans verbosité inutile.

## 📤 Format de Sortie Attendu
Présente la réponse sous forme structurée avec puces, tableaux comparatifs si pertinent, et une synthèse opérationnelle finale."""

    async def generate_prompt_ai(
        self,
        expertise: str,
        mission: str,
        tone: str,
        output_format: str,
        length: str,
        framework: str = "RTF",
        target_model: str = "Universel (Tous LLMs)",
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        custom_instructions: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Génère un prompt optimisé de niveau ingénierie de prompt en utilisant un LLM réel.
        """
        system_meta_prompt = f"""Tu es un ingénieur de prompt d'élite (Lead Prompt Engineer) et un expert en Intelligence Artificielle.
Ton rôle est de concevoir des prompts de niveau entreprise, prêts pour la production, destinés à tirer la meilleure performance des LLMs.

Framework méthodologique sélectionné : {framework} ({self.FRAMEWORKS.get(framework, 'Méthode avancée')}).
Modèle LLM cible : {target_model}.

Directives de génération :
1. Crée un prompt complet, puissant, structuré et directement réutilisable.
2. Définis clairement :
   - Le Persona / Rôle exact
   - Le Contexte et la Mission détaillée
   - Les Consignes opérationnelles étape par étape
   - Les Contraintes négatives (ce qu'il ne faut PAS faire)
   - Le Format de sortie précis attendu
   - Des critères de qualité
3. Adopte le formatage Markdown le plus lisible (sections, puces, balises claires).
4. Ne donne AUCUN blabla avant ou après le prompt généré. Donne DIRECTEMENT le prompt utilisable."""

        user_input_prompt = f"""PARAMÈTRES DE LA DEMANDE :
- Domaine d'expertise : {expertise}
- Mission principale : {mission}
- Ton souhaité : {tone}
- Format de réponse souhaité : {output_format}
- Envergure / Longueur visée : {length}
- Consignes supplémentaires : {custom_instructions or 'Aucune'}

Génère dès maintenant le prompt optimal :"""

        prompt_text, used_model, latency = await self._dispatch_llm(
            system_prompt=system_meta_prompt,
            user_prompt=user_input_prompt,
            provider=provider or settings.DEFAULT_AI_PROVIDER,
            model=model,
            api_key=api_key,
            temperature=temperature,
        )

        # Calculer le nombre estimé de tokens (1 token ≈ 4 caractères en moyenne)
        estimated_tokens = max(1, len(prompt_text) // 4)

        return {
            "titre": f"Prompt {expertise} - {mission[:35]}...",
            "prompt_text": prompt_text,
            "provider": provider or settings.DEFAULT_AI_PROVIDER,
            "model_used": used_model,
            "framework": framework,
            "target_model": target_model,
            "latency_seconds": latency,
            "estimated_tokens": estimated_tokens,
        }

    async def optimize_prompt_ai(
        self,
        prompt_text: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Analyse et réécrit un prompt existant avec un LLM réel pour le perfectionner.
        """
        system_meta_prompt = """Tu es un auditeur et optimiseur expert de prompts IA.
Ton objectif est de prendre le prompt brut d'un utilisateur, d'en analyser les faiblesses (manque de contexte, ambiguïté, absence de contraintes négatives, formatage vague), puis de le réécrire pour en faire une version de niveau professionnel.

Tu dois répondre UNIQUEMENT au format JSON strict avec la structure suivante :
{
  "optimized_prompt": "Le prompt intégralement réécrit et enrichi avec sections et structure",
  "critique": "Analyse critique en 2-3 phrases des faiblesses du prompt original",
  "key_improvements": [
    "Amélioration 1 (ex: ajout de contraintes négatives)",
    "Amélioration 2 (ex: structuration du format de sortie)",
    "Amélioration 3 (ex: précision du rôle et du contexte)"
  ]
}
Assure-toi que la réponse est un JSON valide sans texte superflu."""

        user_input = f"Voici le prompt à auditer et optimiser :\n```\n{prompt_text}\n```"

        raw_response, used_model, latency = await self._dispatch_llm(
            system_prompt=system_meta_prompt,
            user_prompt=user_input,
            provider=provider or settings.DEFAULT_AI_PROVIDER,
            model=model,
            api_key=api_key,
            temperature=temperature,
        )

        # Extraire le JSON de la réponse
        try:
            cleaned = raw_response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            parsed = json.loads(cleaned.strip())
            optimized_prompt = parsed.get("optimized_prompt", prompt_text)
            critique = parsed.get("critique", "Optimisation appliquée par l'IA.")
            key_improvements = parsed.get("key_improvements", ["Structure enrichie", "Contraintes ajoutées"])
        except Exception as e:
            logger.warning(f"Impossible de parser le JSON strict de l'optimiseur IA : {e}. Utilisation directe.")
            optimized_prompt = raw_response
            critique = "Optimisation directe générée par l'agent IA."
            key_improvements = ["Réécriture complète", "Précision des consignes"]

        return {
            "original_prompt": prompt_text,
            "optimized_prompt": optimized_prompt,
            "critique": critique,
            "key_improvements": key_improvements,
            "model_used": used_model,
            "latency_seconds": latency,
        }

    async def test_prompt_sandbox(
        self,
        prompt_template: str,
        user_input_test: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Bac à sable : Exécute le prompt généré contre un vrai LLM avec une entrée utilisateur pour tester son efficacité en direct.
        """
        response_text, used_model, latency = await self._dispatch_llm(
            system_prompt=f"Tu dois te comporter strictement selon les instructions de ce prompt système :\n\n{prompt_template}",
            user_prompt=user_input_test if user_input_test.strip() else "Exécute ta tâche selon le prompt.",
            provider=provider or settings.DEFAULT_AI_PROVIDER,
            model=model,
            api_key=api_key,
            temperature=temperature,
        )

        return {
            "prompt_executed": prompt_template,
            "test_input": user_input_test,
            "response": response_text,
            "model_used": used_model,
            "latency_seconds": latency,
            "estimated_tokens": max(1, len(response_text) // 4),
        }


# Instance singleton
ai_service = AIService()
