"""
Сервис загрузки и построения промптов для LLM.
"""
from pathlib import Path


def load_prompt(prompt_path: str = "prompts/prompt_en.txt") -> str:
    """
    Загружаем расширенный промпт из файла.
    Если файла нет — возвращаем дефолтный промпт.
    """
    prompt_file = Path(prompt_path)
    if prompt_file.exists():
        text = prompt_file.read_text(encoding="utf-8").strip()
        print(f"✅ Загружен кастомный промпт из {prompt_file}")
        return text

    print("⚠️ prompt_en.txt не найден, используем дефолтный промпт")
    return (
        "You are a bot that helps me describe images and videos (in English) for "
        "uploading to stock photo/video websites for commercial sale. "
        "You create descriptions about 200 characters long and exactly 49 keywords. "
        "Your goal is to maximize the commercial sales potential of works on stock websites."
    )


def build_prompt(captions: list[str], user_note: str | None = None) -> str:
    """
    Собираем итоговый промпт:
    - captions: список подписей от BLIP или кадров видео
    - user_note: дополнительный контекст (например, праздник, комментарий)
    """
    base_caption = "; ".join(captions)
    extra = f"\nUser provided context: {user_note}" if user_note else ""
    return f"{load_prompt()}\n\nImage captions: {base_caption}{extra}"
