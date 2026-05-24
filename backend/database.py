import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

# Chemin vers la base de données
DB_PATH = Path(__file__).parent.parent / "prompts.db"


def init_db() -> None:
    """Initialise la base SQLite avec la table 'prompts'."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prompts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titre TEXT NOT NULL,
        categorie TEXT NOT NULL,
        prompt_text TEXT NOT NULL,
        score INTEGER DEFAULT 0
    )
    ''')
    
    conn.commit()
    conn.close()


def save_prompt(titre: str, categorie: str, prompt_text: str, score: int) -> int:
    """
    Sauvegarde un prompt dans la base de données.
    
    Args:
        titre: Titre du prompt
        categorie: Catégorie du prompt
        prompt_text: Contenu du prompt
        score: Score de qualité (0-100)
    
    Returns:
        ID du prompt inséré
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO prompts (titre, categorie, prompt_text, score)
    VALUES (?, ?, ?, ?)
    ''', (titre, categorie, prompt_text, score))
    
    conn.commit()
    prompt_id = cursor.lastrowid
    conn.close()
    
    return prompt_id


def get_all_prompts(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        'SELECT id, titre, categorie, prompt_text, score FROM prompts ORDER BY id DESC LIMIT ? OFFSET ?',
        (limit, offset)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def count_prompts() -> int:
    conn = sqlite3.connect(DB_PATH)
    total = conn.execute('SELECT COUNT(*) FROM prompts').fetchone()[0]
    conn.close()
    return total


def search_prompts(query: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    pattern = f'%{query}%'
    rows = conn.execute(
        'SELECT id, titre, categorie, prompt_text, score FROM prompts WHERE titre LIKE ? OR prompt_text LIKE ? ORDER BY id DESC LIMIT ? OFFSET ?',
        (pattern, pattern, limit, offset)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def count_search_prompts(query: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    pattern = f'%{query}%'
    total = conn.execute(
        'SELECT COUNT(*) FROM prompts WHERE titre LIKE ? OR prompt_text LIKE ?',
        (pattern, pattern)
    ).fetchone()[0]
    conn.close()
    return total


def get_prompt_by_id(prompt_id: int) -> Optional[Dict[str, Any]]:
    """Récupère un prompt spécifique par son ID."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, titre, categorie, prompt_text, score FROM prompts WHERE id = ?', (prompt_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def delete_prompt(prompt_id: int) -> bool:
    """Supprime un prompt de la base de données."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM prompts WHERE id = ?', (prompt_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    
    return success
