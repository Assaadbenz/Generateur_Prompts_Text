"""
Configuration du système de logging professionnel pour l'application.
Prend en charge la journalisation console et fichier avec rotation.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from backend.config import settings


def setup_logger(name: str = "app") -> logging.Logger:
    """Configure et retourne un logger avec formatage propre pour console et fichier."""
    logger = logging.getLogger(name)
    
    # Éviter les handlers en double si la fonction est appelée plusieurs fois
    if logger.handlers:
        return logger
        
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Formatage détaillé
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 1. Handler Console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 2. Handler Fichier tournant (max 5 MB, 3 backups)
    try:
        log_file = Path(settings.LOG_FILE)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            str(log_file),
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Avertissement : impossible de configurer le fichier de log : {e}", file=sys.stderr)
        
    return logger


logger = setup_logger("prompt_generator")
