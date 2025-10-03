import json
from pathlib import Path
from typing import List

HOLIDAYS_DIR = Path(__file__).parent / "holidays"

# список всех тем
HOLIDAY_TOPICS = [
    "animals",
    "health",
    "family",
    "business",
    "environment",
    "food",
    "culture",
    "tech",
    "sports",
    "education",
]

def load_holidays(topic: str) -> List[str]:
    """
    Загружает список праздников по теме.
    """
    file_path = HOLIDAYS_DIR / f"{topic}.json"
    if not file_path.exists():
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def find_related_holidays(keywords: List[str], topic: str) -> List[str]:
    """
    Возвращает список праздников, связанных с ключевыми словами в одной теме.
    Совпадение — по подстроке (например, 'dog' → 'International Dog Day').
    """
    holidays = load_holidays(topic)
    result = []
    for kw in keywords:
        for holiday in holidays:
            if kw.lower() in holiday.lower() and holiday not in result:
                result.append(holiday)
    return result[:5]  # ограничиваем, чтобы не захламлять

def find_all_related(keywords: List[str]) -> List[str]:
    """
    Возвращает список праздников, связанных с ключевыми словами,
    проверяя все темы (animals, health, family, food и т. д.).
    """
    result = []
    for topic in HOLIDAY_TOPICS:
        holidays = find_related_holidays(keywords, topic)
        for h in holidays:
            if h not in result:
                result.append(h)
    return result[:10]  # ограничиваем итоговый список
