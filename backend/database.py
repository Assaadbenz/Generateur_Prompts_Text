import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

DB_PATH = Path(__file__).parent.parent / "prompts.db"
logger = logging.getLogger(__name__)


@contextmanager
def get_db():
    """Get database connection with timeout and proper error handling."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        conn.row_factory = sqlite3.Row
        yield conn
        conn.commit()
    except sqlite3.DatabaseError as e:
        logger.error(f"Database error: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error in database operation: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise
    finally:
        if 'conn' in locals():
            conn.close()


def init_db() -> None:
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
    with get_db() as conn:
        cursor = conn.execute(
            'INSERT INTO prompts (titre, categorie, prompt_text, score) VALUES (?, ?, ?, ?)',
            (titre, categorie, prompt_text, score)
        )
        return cursor.lastrowid


def get_all_prompts(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            'SELECT id, titre, categorie, prompt_text, score FROM prompts ORDER BY id DESC LIMIT ? OFFSET ?',
            (limit, offset)
        ).fetchall()
    return [dict(row) for row in rows]


def count_prompts() -> int:
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
