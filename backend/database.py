# ============================================================================
# GESTION DE LA BASE DE DONNÉES SQLITE
# ============================================================================
# Ce fichier gère toutes les opérations avec la base de données SQLite
# SQLite est un système de gestion de base de données léger, parfait pour 
# les petits projets

import sqlite3  # Module standard Python pour SQLite
from contextlib import contextmanager  # Gestionnaire de contexte Python
from pathlib import Path  # Gestion des chemins de fichiers
from typing import List, Dict, Any, Optional  # Types pour les annotations
import logging  # Enregistrement des messages d'erreur

# Chemin vers la base de données: dossier parent + "prompts.db"
# Path(__file__).parent.parent remonte d'un niveau depuis ce fichier
DB_PATH = Path(__file__).parent.parent / "prompts.db"

# Logger pour enregistrer les erreurs de base de données
logger = logging.getLogger(__name__)


@contextmanager
def get_db():
    """Gérateur de contexte pour les connexions à la base de données.
    
    Avantage: Ferme automatiquement la connexion, même en cas d'erreur.
    Utilisation: with get_db() as conn:
    
    Paramètres:
    - timeout=10.0: attend 10 secondes si la BD est verrouillée
    - row_factory=sqlite3.Row: retourne les lignes comme des dictionnaires
    """
    try:
        # Créer une connexion à la BD SQLite
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        # Retourner les lignes comme des objets Row (lisibles comme des dicts)
        conn.row_factory = sqlite3.Row
        yield conn  # "yield" rend cette fonction réutilisable
        conn.commit()  # Valider les changements
    except sqlite3.DatabaseError as e:
        # Si erreur de base de données, enregistrer et annuler
        logger.error(f"Database error: {e}")
        if 'conn' in locals():
            conn.rollback()  # Annuler les changements
        raise
    except Exception as e:
        # Si autre erreur, enregistrer et annuler
        logger.error(f"Unexpected error in database operation: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise
    finally:
        # Toujours fermer la connexion (with ou sans erreur)
        if 'conn' in locals():
            conn.close()



def init_db() -> None:
    """Initialise la base de données en créant la table 'prompts'.
    
    La clause IF NOT EXISTS évite une erreur si la table existe déjà.
    
    Colonnes de la table:
    - id: clé primaire, auto-incrémenté
    - titre: nom du prompt
    - categorie: domaine/catégorie
    - prompt_text: contenu du prompt
    - score: score de qualité (0-100)
    """
    with get_db() as conn:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT NOT NULL,
            categorie TEXT NOT NULL,
            prompt_text TEXT NOT NULL,
            score INTEGER DEFAULT 0
        )
        ''')



def save_prompt(titre: str, categorie: str, prompt_text: str, score: int) -> int:
    """Sauvegarde un nouveau prompt dans la base de données.
    
    Paramètres:
    - titre: nom du prompt
    - categorie: domaine/catégorie du prompt
    - prompt_text: contenu complet du prompt
    - score: score de qualité (0-100)
    
    Retourne: l'ID du prompt créé
    """
    with get_db() as conn:
        cursor = conn.execute(
            # ? = paramètres pour éviter les injections SQL
            'INSERT INTO prompts (titre, categorie, prompt_text, score) VALUES (?, ?, ?, ?)',
            (titre, categorie, prompt_text, score)
        )
        return cursor.lastrowid  # Retourne l'ID auto-incrémenté



def get_all_prompts(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """Récupère une liste de prompts avec pagination.
    
    Paramètres:
    - limit: nombre maximum de prompts à retourner (par défaut 50)
    - offset: nombre de prompts à sauter (pour la pagination)
    
    Exemple: get_all_prompts(limit=10, offset=20) retourne les prompts 21-30
    
    Retourne: liste de dictionnaires contenant les données des prompts
    """
    with get_db() as conn:
        # ORDER BY id DESC = affiche les plus récents en premier
        rows = conn.execute(
            'SELECT id, titre, categorie, prompt_text, score FROM prompts ORDER BY id DESC LIMIT ? OFFSET ?',
            (limit, offset)
        ).fetchall()  # Retourner tous les résultats
    # Convertir les objets Row en dictionnaires
    return [dict(row) for row in rows]



def count_prompts() -> int:
    """Compte le nombre total de prompts dans la base de données.
    
    Retourne: nombre total de prompts
    """
    with get_db() as conn:
        return conn.execute('SELECT COUNT(*) FROM prompts').fetchone()[0]


def search_prompts(query: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    with get_db() as conn:
        pattern = f'%{query}%'
        rows = conn.execute(
            'SELECT id, titre, categorie, prompt_text, score FROM prompts WHERE titre LIKE ? OR prompt_text LIKE ? ORDER BY id DESC LIMIT ? OFFSET ?',
            (pattern, pattern, limit, offset)
        ).fetchall()
    return [dict(row) for row in rows]


def count_search_prompts(query: str) -> int:
    with get_db() as conn:
        pattern = f'%{query}%'
        return conn.execute(
            'SELECT COUNT(*) FROM prompts WHERE titre LIKE ? OR prompt_text LIKE ?',
            (pattern, pattern)
        ).fetchone()[0]


def get_prompt_by_id(prompt_id: int) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        row = conn.execute(
            'SELECT id, titre, categorie, prompt_text, score FROM prompts WHERE id = ?',
            (prompt_id,)
        ).fetchone()
    return dict(row) if row else None


def delete_prompt(prompt_id: int) -> bool:
    with get_db() as conn:
        conn.execute('DELETE FROM prompts WHERE id = ?', (prompt_id,))
        return conn.total_changes > 0
