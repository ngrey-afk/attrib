"""
Быстрый поиск по словарю Getty (локальный SQLite).
"""

import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path("output/vocab.db")

class GettyVocab:
    def __init__(self, db_path: str = DB_PATH):
        if not Path(db_path).exists():
            raise RuntimeError("Vocabulary DB not found. Run vocab_loader first.")
        self.conn = sqlite3.connect(db_path)

    def lookup(self, term: str) -> Optional[dict]:
        """
        Ищет термин или его альтернативы.
        Возвращает dict с preferred_label и uri, если найдено.
        """
        cur = self.conn.cursor()

        # точное совпадение с preferred_label
        cur.execute(
            "SELECT preferred_label, uri FROM vocab_entry WHERE term = ? COLLATE NOCASE",
            (term,)
        )
        row = cur.fetchone()
        if row:
            return {"preferred": row[0], "uri": row[1]}

        # поиск по alt_label
        cur.execute("""
            SELECT v.preferred_label, v.uri
              FROM vocab_entry v
              JOIN alt_label a ON a.entry_id = v.id
             WHERE a.alt = ? COLLATE NOCASE
        """, (term,))
        row2 = cur.fetchone()
        if row2:
            return {"preferred": row2[0], "uri": row2[1]}

        return None
