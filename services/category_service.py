from domain.categories import SHUTTERSTOCK_CATEGORIES

def detect_category(keywords: list[str], stock: str = "shutterstock") -> str:
    """Определяет категорию по ключевым словам"""
    kws = [kw.lower() for kw in keywords]
    categories = SHUTTERSTOCK_CATEGORIES if stock == "shutterstock" else SHUTTERSTOCK_CATEGORIES
    for cat, terms in categories.items():
        if any(term in kws for term in terms):
            return cat
    return "Uncategorized"
