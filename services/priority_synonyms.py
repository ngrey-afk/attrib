import json
from pathlib import Path

def load_priority_synonyms() -> dict[str, list[str]]:
    file_path = Path(__file__).parent / "priority_synonym.json"
    if not file_path.exists():
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

priority_synonyms = load_priority_synonyms()
