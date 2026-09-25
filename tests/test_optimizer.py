"""
Tests unitaires pour le moteur d'évaluation et de scoring des prompts.
"""

from backend.optimizer import (
    calculate_quality_score,
    get_score_breakdown,
    optimize_prompt,
)


def test_empty_prompt_score():
    """Un prompt vide doit avoir un score de 0."""
    assert calculate_quality_score("") == 0
    assert calculate_quality_score("   ") == 0


def test_high_quality_prompt_score():
    """Un prompt bien structuré avec rôle, mission, consignes, format et spécificité doit avoir un score élevé."""
    prompt = """Tu es un expert chevronné en cybersécurité offensive.

Mission :
Réalise un audit d'architecture sécurisée pour une application bancaire destinée aux professionnels.

Consignes opérationnelles :
1. Identifie au moins 5 vecteurs d'attaque critiques (OWASP Top 10).
2. Propose des contre-mesures obligatoires pour chacun.
3. Ne divulgue jamais d'exploits malveillants directement exécutables.

Format attendu :
Présente un tableau comparatif avec les colonnes : Risque, Impact, Remédiation."""

    score = calculate_quality_score(prompt)
    assert score >= 75
    breakdown = get_score_breakdown(prompt)
    assert breakdown["total"] == score
    assert breakdown["breakdown"]["Structure"]["score"] >= 30


def test_optimizer_suggestions():
    """Un prompt court sans structure doit recevoir des suggestions pertinentes."""
    short_prompt = "Écris-moi un texte sur le soleil."
    result = optimize_prompt(short_prompt)
    assert result["score"] < 50
    assert len(result["suggestions"]) > 0
