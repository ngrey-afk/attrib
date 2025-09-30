"""
Здесь будут шаблоны промптов для LLM.
Пока оставлено как заготовка.
"""
from pathlib import Path

class PromptService:
    def __init__(self, prompt_path: str = "prompts/prompt_en.txt"):
        self.template = Path(prompt_path).read_text(encoding="utf-8")

    def build_prompt(self, captions: list[str], user_note: str | None = None) -> str:
        """
        Создаём полный промпт для LLM (описание + ключи)
        - captions: список подписей от BLIP
        - user_note: текст, который пользователь явно указал (например, праздник)
        """
        base_caption = "; ".join(captions)
        extra = f"\nUser provided context: {user_note}" if user_note else ""
        return f"{self.template}\n\nImage captions: {base_caption}{extra}"


def build_prompt(captions: list) -> str:
    return " ".join(captions)
