from pathlib import Path
from transformers import pipeline

# Загружаем расширенный промпт из файла
PROMPT_FILE = Path("prompts/prompt_en.txt")
if PROMPT_FILE.exists():
    PROMPT_TEMPLATE = PROMPT_FILE.read_text(encoding="utf-8").strip()
    print(f"✅ Загружен кастомный промпт из {PROMPT_FILE}")
else:
    # fallback — если файла нет
    PROMPT_TEMPLATE = (
        "You are a bot that helps me describe images and videos for stock websites. "
        "Create an English description (max 200 characters) and exactly 49 keywords."
    )
    print("⚠️ Внимание: файл prompt_en.txt не найден, используется fallback-промпт!")

# Загружаем LLM для генерации
generator = pipeline("text-generation", model="microsoft/phi-3-mini-4k-instruct")


def generate_keywords_with_prompt(prompt: str, caption: str, **kwargs) -> dict:
    """
    Генерация описания и ключевых слов на основе расширенного промпта и caption от BLIP.
    Возвращает dict: {"title": ..., "description": ..., "keywords": [...]}
    """
    full_prompt = f"{PROMPT_TEMPLATE}\n\nImage/Video content: {caption}\n\n{prompt.strip()}"

    print("📝 Отправляем запрос в модель...")
    result = generator(full_prompt, max_new_tokens=400, temperature=0.7, do_sample=True)
    text = result[0]["generated_text"]

    # Простейший парсер: описание до первой пустой строки, потом список ключей
    parts = text.split("\n\n")
    description = parts[0].strip() if parts else ""
    keywords = []
    if len(parts) > 1:
        keywords = [
            kw.strip().lower()
            for kw in parts[1].replace("\n", " ").split(",")
            if kw.strip()
        ]

    print(f"✅ Сгенерировано описание: {description[:60]}...")
    print(f"✅ Ключевых слов: {len(keywords)}")

    return {
        "title": description[:80].strip().capitalize(),
        "description": description,
        "keywords": keywords[:49],
    }


def generate_metadata_with_prompt(prompt: str, caption: str, **kwargs) -> dict:
    """
    Совместимость: старое имя функции.
    Теперь принимает любые доп. аргументы (например, file_name),
    чтобы не падало при вызове из других сервисов.
    """
    return generate_keywords_with_prompt(prompt, caption, **kwargs)
