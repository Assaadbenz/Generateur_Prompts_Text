"""
Configuration centralisée pour l'application Générateur de Prompts IA.
Gère les variables d'environnement, les clés API et les paramètres par défaut.
"""

import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# Charger le fichier .env depuis la racine du projet
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    # Répertoires
    ROOT_DIR: Path = PROJECT_ROOT
    BACKEND_DIR: Path = PROJECT_ROOT / "backend"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"
    
    # API FastAPI
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_RELOAD: bool = os.getenv("API_RELOAD", "true").lower() in ("true", "1", "yes")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        origin.strip() 
        for origin in os.getenv(
            "ALLOWED_ORIGINS", 
            "http://localhost:8501,http://127.0.0.1:8501,http://localhost:8000,http://127.0.0.1:8000"
        ).split(",")
        if origin.strip()
    ]
    
    # Base de données
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", str(PROJECT_ROOT / "prompts.db"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", str(LOGS_DIR / "app.log"))
    
    # Fournisseurs d'IA (LLMs)
    DEFAULT_AI_PROVIDER: str = os.getenv("DEFAULT_AI_PROVIDER", "mock")  # 'gemini', 'openai', 'groq', 'ollama', 'mock'
    
    # Clés d'API
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    
    # Endpoints et modèles par défaut
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")
    
    # Timeouts (secondes)
    AI_TIMEOUT_SECONDS: float = float(os.getenv("AI_TIMEOUT_SECONDS", "30.0"))


settings = Settings()

# Assurer que le dossier logs existe
settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
