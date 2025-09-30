"""
Модуль для загрузки словаря Getty (AAT/TGN/ULAN) в локальную SQLite базу.
Работает только с английскими терминами.
"""

import sqlite3
from pathlib import Path
from rdflib import Graph, Namespace

DB_PATH = Path("output/vocab.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS vocab_entry (
        id INTEGER PRIMARY KEY,
        term TEXT COLLATE NOCASE,
        preferred_label TEXT,
        uri TEXT,
        vocabulary TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alt_label (
        entry_id INTEGER,
        alt TEXT COLLATE NOCASE,
        FOREIGN KEY(entry_id) REFERENCES vocab_entry(id)
    )
    """)
    conn.commit()
    conn.close()

def load_rdf_to_db(rdf_file: str, vocab_name: str = "AAT"):
    """
    Загружает RDF/XML или N-Triples файл в SQLite.
    Берём только английские prefLabel/altLabel.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    g = Graph()
    g.parse(rdf_file)

    SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")

    for s, p, o in g.triples((None, SKOS.prefLabel, None)):
        if getattr(o, "language", None) == "en":
            uri = str(s)
            preferred = str(o)
            cur.execute(
                "INSERT INTO vocab_entry(term, preferred_label, uri, vocabulary) VALUES (?, ?, ?, ?)",
                (preferred, preferred, uri, vocab_name)
            )
            entry_id = cur.lastrowid

            # altLabels
            for _, _, alt in g.triples((s, SKOS.altLabel, None)):
                if getattr(alt, "language", None) == "en":
                    cur.execute(
                        "INSERT INTO alt_label(entry_id, alt) VALUES (?, ?)",
                        (entry_id, str(alt))
                    )

    conn.commit()
    conn.close()
    print(f"✔ Loaded vocabulary from {rdf_file} into {DB_PATH}")
