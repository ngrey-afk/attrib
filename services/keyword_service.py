import subprocess
import re
from services.priority_synonyms import priority_synonyms
from services.description_service import enrich_description_with_holidays, enrich_keywords_with_holidays
import difflib


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
        f"Rephrase this caption into a clean extended title of 7–12 words: {caption}. "
        f"Do not copy the caption word-for-word. "
        f"Make it natural, professional, and relevant for commercial usage. "
        f"Output must be only the title, no comments, no explanations."
    )
    raw = call_ollama("gemma2:2b", prompt)
    return raw.split("\n")[0].strip('" ') if raw else caption


def generate_description(caption: str, media_type: str) -> str:
    original_caption = caption.strip()

    prompt = (
        f"You are generating a DESCRIPTION for stock photo/video metadata.\n"
        f"Caption (repeat exactly, do not change or rephrase): {original_caption}\n\n"
        f"RULES:\n"
        f"- Start with the caption EXACTLY as written.\n"
        f"- After the caption, add a comma, then continue with 3–5 THEMES.\n"
        f"- THEMES must be short semantic/commercial phrases (2–3 words).\n"
        f"- Optionally add 1–2 real international or thematic observances if clearly relevant.\n"
        f"- Output must be ONE single line: caption + themes + observances.\n"
        f"- No filler words, no explanations, no 'caption' markers.\n"
        f"- Only commas and periods as punctuation.\n"
        f"- Max 200 characters.\n"
    )

    raw = call_ollama("gemma2:2b", prompt)
    if not raw:
        return original_caption

    desc = raw.strip('" ').replace("\n", " ").replace(" a ", " ").replace(" the ", " ").replace("The ", "").replace("A ", "")
    desc = desc.encode("ascii", "ignore").decode("ascii")  # чистим эмодзи и нелатиницу
    # чистим кавычки и артикли

    return desc


def generate_keywords(caption: str, media_type: str, description: str = "") -> list[str]:
    """Генерация 49 релевантных ключей с приоритетом по смыслу (просто и стабильно)."""

    # --- 1. Базовые слова из кэпшона ---
    words = re.findall(r"\b[a-zA-Z]+\b", caption.lower())
    base_words = [w for w in words if len(w) > 2][:10]

    # --- 2. Подмешиваем приоритетные синонимы ---
    expanded = []
    for w in base_words:
        expanded.append(w)
        if w in priority_synonyms:
            expanded.extend(priority_synonyms[w])
    expanded = list(dict.fromkeys(expanded))

    # --- 3. Один промпт к нейросети ---
    prompt = (
        f"You are generating stock photo/video metadata keywords.\n"
        f"Caption: {caption}\n"
        f"Description: {description}\n\n"
        f"RULES:\n"
        f"- Generate up to 100 short keywords (single words or 2-word phrases).\n"
        f"- Use commercial, visual, and thematic relevance.\n"
        f"- Avoid duplicates and filler words.\n"
        f"- No sentences, no reasoning.\n"
        f"- Output only comma-separated lowercase keywords."
    )

    raw = call_ollama("gemma2:2b", prompt)
    keywords = [w.strip().lower() for w in raw.split(",") if w.strip()] if raw else []

    # --- 4. Добавляем наши приоритетные термины ---
    keywords = expanded + keywords

    # --- 5. Фильтрация и сортировка по релевантности ---
    banned = {"photo", "image", "stock", "photography", "here", "words", "generated"}
    keywords = [k for k in keywords if k not in banned and len(k) > 2]

    # Удаляем дубли и слишком похожие слова
    unique = []
    for k in keywords:
        if not any(difflib.SequenceMatcher(None, k, u).ratio() > 0.85 for u in unique):
            unique.append(k)

    # --- 6. Сортировка — более короткие и частотные в начале ---
    unique.sort(key=lambda x: (len(x), x))

    # --- 7. Ограничение до 49 ключей ---
    final_keywords = unique[:49]

    return final_keywords


def generate_metadata_with_prompt(caption: str, media_type: str = "image", callback=None) -> dict:
    """Генерация метаданных (title, description, keywords) построчно с анимацией."""
    results = {}

    try:
        # 1. Title
        title = generate_title(caption, media_type)
        if callback and title:
            callback("title", title)
        results["title"] = title

        # 2. Description
        desc = generate_description(caption, media_type)
        themes = [t.strip().lower() for t in desc.split(",") if t.strip()]
        desc = enrich_description_with_holidays(desc, themes)
        if callback and desc:
            callback("description", desc)
        results["description"] = desc

        # 3. Keywords
        keywords = generate_keywords(caption, media_type)
        keywords = enrich_keywords_with_holidays(keywords, themes)
        if callback and keywords:
            callback("keywords", ", ".join(keywords))
        results["keywords"] = keywords

        # 4. Category (сразу после keywords)
        from services.category_service import detect_category
        category = detect_category(keywords)
        if callback and category:
            callback("category", category)
        results["category"] = category

    except Exception as e:
        print(f"❌ Ошибка в generate_metadata_with_prompt: {e}")

    return results