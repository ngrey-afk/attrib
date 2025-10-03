from services.holidays_service import find_all_related

def enrich_description_with_holidays(base_desc: str, themes: list[str], max_len: int = 200) -> str:
    """
    Добавляет к описанию релевантный праздник, если помещается в лимит символов.
    """
    holidays = find_all_related(themes)
    if not holidays:
        return base_desc

    # Берём первый приоритетный праздник
    for holiday in holidays:
        candidate = f"{base_desc}, {holiday}"
        if len(candidate) <= max_len:
            return candidate
    return base_desc  # если ничего не влезло

def enrich_keywords_with_holidays(base_keywords: list[str], themes: list[str]) -> list[str]:
    """
    Добавляет праздники в ключевые слова (нормализуя их).
    """
    holidays = find_all_related(themes)
    if not holidays:
        return base_keywords

    extra_keywords = []
    for holiday in holidays:
        # Оставляем только суть, убираем 'international', 'day', 'world', 'national'
        words = [
            w.lower() for w in holiday.replace("'", "").split()
            if w.lower() not in {"international", "national", "world", "day"}
        ]
        extra_keywords.extend(words)

    # Убираем дубликаты, сохраняем до 49
    combined = list(dict.fromkeys(base_keywords + extra_keywords))
    return combined[:49]
