# services/category_service.py
from domain.categories import SHUTTERSTOCK_CATEGORIES

def detect_category(keywords: list[str], stock: str = "shutterstock") -> str:
    """
    Определяет категорию для ключевых слов.
    :param keywords: список ключевых слов
    :param stock: название стока (shutterstock, adobe и т.д.)
    """
    kws = [kw.lower() for kw in keywords]

    if stock == "shutterstock":
        categories = SHUTTERSTOCK_CATEGORIES
    else:
        categories = SHUTTERSTOCK_CATEGORIES  # fallback

    for category, terms in categories.items():
        if any(term in kws for term in terms):
            return category
    return "Other"
