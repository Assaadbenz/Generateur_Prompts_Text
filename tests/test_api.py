"""
Tests d'intégration complets pour l'API FastAPI Générateur de Prompts IA.
Valide les endpoints de santé, génération, optimisation, persistance et export.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Initialise la base de données avant chaque test."""
    init_db()


def test_root_endpoint():
    """Vérifie le point d'entrée racine."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_health_endpoint():
    """Vérifie le statut de santé du service."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_generate_prompt_ai(monkeypatch):
    """Vérifie la génération de prompt avec l'IA."""
    def fake_generate(**kwargs):
        return """Tu es un Expert Senior en Data Science et Machine Learning.
        
Contexte : Analyse du churn client.
Directives :
1. Prépare les données.
2. Évalue les modèles de classification.
Format : Texte structuré."""

    import gemini_service
    monkeypatch.setattr(gemini_service, "generate_prompt_ai", fake_generate)

    payload = {
        "expertise": "Data Science",
        "mission": "Créer un modèle de prédiction du churn client",
        "tone": "Neutre",
        "output_format": "Texte",
        "length": "Moyenne"
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "prompt_text" in data
    assert len(data["prompt_text"]) > 50
    assert "score" in data
    assert 0 <= data["score"] <= 100


def test_optimize_prompt_ai(monkeypatch):
    """Vérifie l'optimisation d'un prompt existant."""
    def fake_optimize(prompt_text, api_key=None):
        return {
            "optimized_prompt": f"Tu es un expert.\n\nMission : {prompt_text}\n\nConsignes : 1. Analyser.",
            "suggestions": ["Précision du rôle", "Ajout de contraintes"]
        }

    import gemini_service
    monkeypatch.setattr(gemini_service, "optimize_prompt_ai", fake_optimize)

    payload = {
        "prompt_text": "Rédige-moi un rapport sur les ventes du mois dernier."
    }
    response = client.post("/optimize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "optimized_prompt" in data
    assert "score" in data
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)


def test_prompt_crud_and_search_flow():
    """Vérifie le cycle de vie complet d'un prompt : Sauvegarde -> Lecture -> Recherche -> Suppression."""
    # 1. Sauvegarde
    save_payload = {
        "titre": "Test Prompt Automated CI",
        "prompt_text": "Tu es un architecte Cloud AWS senior. Définis un modèle Terraform pour VPC multi-AZ.",
        "score": 90
    }
    create_res = client.post("/prompts/save", json=save_payload)
    assert create_res.status_code == 200
    prompt_id = create_res.json()["id"]
    assert prompt_id > 0

    # 2. Lecture par ID
    get_res = client.get(f"/prompts/{prompt_id}")
    assert get_res.status_code == 200
    prompt = get_res.json()
    assert prompt["titre"] == "Test Prompt Automated CI"

    # 3. Recherche
    search_res = client.get("/prompts/search", params={"q": "Terraform"})
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["total"] >= 1
    assert any(p["id"] == prompt_id for p in search_data["prompts"])

    # 4. Suppression
    del_res = client.delete(f"/prompts/{prompt_id}")
    assert del_res.status_code == 200

    # 5. Vérification de la suppression
    get_deleted = client.get(f"/prompts/{prompt_id}")
    assert get_deleted.status_code == 404


def test_export_endpoints():
    """Vérifie les exports JSON et Markdown."""
    # JSON
    res_json = client.get("/export/json")
    assert res_json.status_code == 200
    assert "application/json" in res_json.headers["content-type"]

    # Markdown
    res_md = client.get("/export/markdown")
    assert res_md.status_code == 200
    assert "text/markdown" in res_md.headers["content-type"]
