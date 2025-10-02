import json
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


def call_ollama(model: str, prompt: str) -> str:
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return result.stdout.decode("utf-8").strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Ollama error: {e.stderr.decode('utf-8')}")
        return ""


def generate_title(caption: str, media_type: str) -> str:
    prompt = (
        f"You are generating an English title for photo/video metadata. "
        f"Rephrase this caption into a clean extended  of 7–12 words: {caption}. "
        f"Do not copy the caption word-for-word. "
        f"Make it natural, professional, and relevant for commercial usage. "
        f"Output must be only the title, no comments, no explanations."
    )
    raw = call_ollama("llama3", prompt)
    return raw.split("\n")[0].strip('" ') if raw else caption


def generate_description(caption: str, media_type: str) -> str:
    prompt = (
        f"You are generating an English description for photo/video metadata. "
        f"Start exactly with this caption, unchanged: {caption}. "
        f"After it, continue in a short list style: 3–5 key themes separated by commas. "
        f"Focus on subject, setting, and commercial use (e.g. pet care, veterinarian, medical). "
        f"Optionally add 1–2 real international or thematic observances (e.g. World Dog Day, International Friendship Day), "
        f"only if they clearly match the caption. "
        f"Do not use generic words like 'holiday' or 'festival'. "
        f"Do not add filler text, do not write full sentences, no introductions, no quotes. "
        f"Forbidden: 'concept for', 'ideal for', 'perfect for', 'showcasing'. "
        f"Output must be only the description, no comments, no explanations. "
        f"Remove articles 'a', 'the'. "
        f"Max 200 characters."
    )
    raw = call_ollama("llama3", prompt)
    if not raw:
        return caption

    # чистим кавычки и артикли
    desc = raw.strip('" ').replace(" a ", " ").replace(" the ", " ").replace("The ", "").replace("A ", "")
    return desc




def generate_keywords(caption: str, media_type: str) -> list[str]:
    prompt = (
        f"Generate exactly 49 unique, lowercase, comma-separated single words in English. "
        f"Base with this exact caption: \"{caption}\". "
        f"No numbering, no explanations. "
        f"First 10 must describe main objects, actions, background, holidays or businesses. "
        f"Include synonyms. "
        f"Do not use words like 'photo', 'photography', 'image', 'stock'. "
        f"Each word only once. "
        f"Caption: {caption}\nType: {media_type}"
    )
    raw = call_ollama("llama3", prompt)
    if not raw:
        return []

    keywords = [w.strip() for w in raw.split(",") if w.strip()]
    if len(keywords) < 49:
        missing = 49 - len(keywords)
        prompt2 = (
            f"Generate {missing} additional unique synonyms or closely related words. "
            f"Only output lowercase, comma-separated words, no comments. "
            f"Base set: {', '.join(keywords)}"
        )
        raw2 = call_ollama("llama3", prompt2)
        extra = [w.strip().lower() for w in raw2.split(",") if w.strip()]
        keywords = list(dict.fromkeys(keywords + extra))

    return keywords[:49]


def generate_metadata_with_prompt(caption: str, media_type: str = "image", callback=None) -> dict:
    """
    Генерация метаданных (title, description, keywords).
    Callback вызывается по мере готовности каждого поля.
    Работает асинхронно, без join(), чтобы не блокировать UI.
    """
    results = {"title": "", "description": "", "keywords": []}
    lock = threading.Lock()

    def run_title():
        try:
            title = generate_title(caption, media_type)
            with lock:
                results["title"] = title
            print(f"📝 Title generated: {title}")
            if callback and title:
                callback("title", title)
        except Exception as e:
            print(f"❌ Ошибка в generate_title: {e}")

    def run_description():
        try:
            desc = generate_description(caption, media_type)
            with lock:
                results["description"] = desc
            print(f"📝 Description generated: {desc}")
            if callback and desc:
                callback("description", desc)
        except Exception as e:
            print(f"❌ Ошибка в generate_description: {e}")

    def run_keywords():
        try:
            keywords = generate_keywords(caption, media_type)
            with lock:
                results["keywords"] = keywords
            print(f"📝 Keywords count: {len(keywords)}")
            if callback and keywords:
                callback("keywords", ", ".join(keywords))
                # вычисляем категорию сразу после появления ключевых слов
                from services.category_service import detect_category
                category = detect_category(keywords)
                if callback and category:
                    callback("category", category)
        except Exception as e:
            print(f"❌ Ошибка в generate_keywords: {e}")

    # Запускаем три параллельных потока
    threading.Thread(target=run_title, daemon=True).start()
    threading.Thread(target=run_description, daemon=True).start()
    threading.Thread(target=run_keywords, daemon=True).start()

    # Возвращаем сразу (пустой/частичный результат), UI обновится через callback
    return results
