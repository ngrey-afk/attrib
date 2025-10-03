import subprocess
import re
from services.description_service import enrich_description_with_holidays, enrich_keywords_with_holidays


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




def generate_keywords(caption: str, media_type: str) -> list[str]:
    stopwords = {
        "a","the","and","with","on","in","of","to","for","by","at","is","are",
        "was","were","this","that","these","those","it","its","an","as","one",
        "here","there","them","those","someone","some","any"
    }

    # --- 1. базовые объекты ---
    words = re.findall(r"\b[a-zA-Z]+\b", caption.lower())
    objects = [w for w in words if w not in stopwords and len(w) > 2]
    base_words = list(dict.fromkeys(objects))[:10]

    # --- 2. темы ---
    prompt_themes = (
        f"Extract 3–5 high-level thematic categories for these objects: {', '.join(base_words)}. "
        f"Examples: animal, medical, technology, travel, business. "
        f"Output only lowercase, comma-separated words. No explanations."
    )
    raw_themes = call_ollama("gemma2:2b", prompt_themes)
    themes = [w.strip().lower() for w in raw_themes.split(",") if w.strip()] if raw_themes else []

    # --- 3. синонимы ---
    prompt_synonyms = (
        f"Generate synonyms or closely related words for these objects: {', '.join(base_words)}. "
        f"Only lowercase, comma-separated single words. No sentences."
    )
    raw_syn = call_ollama("gemma2:2b", prompt_synonyms)
    synonyms = [w.strip().lower() for w in raw_syn.split(",") if w.strip()] if raw_syn else []

    # --- 4. бизнес-контекст ---
    prompt_business = (
        f"List 5–8 relevant industries, businesses, or commercial contexts for these objects: {', '.join(base_words)}. "
        f"Examples: veterinary, pet care, healthcare, education, IT, marketing. "
        f"Output lowercase, comma-separated, max 2 words each. No explanations."
    )
    raw_business = call_ollama("gemma2:2b", prompt_business)
    business_words = [w.strip().lower() for w in raw_business.split(",") if w.strip()] if raw_business else []

    # --- 5. объединяем ---
    keywords = base_words + themes + synonyms + business_words

    # --- 6. фильтрация ---
    banned = {"photo", "image", "stock", "photography", "here", "words", "generated"}
    keywords = [w for w in keywords if w not in banned and len(w) > 2]
    keywords = list(dict.fromkeys(keywords))  # уникальные

    # --- 7. добивка до 49 ---
    if len(keywords) < 49:
        prompt_fill = (
            f"Generate {49 - len(keywords)} additional unique related words to these: {', '.join(keywords)}. "
            f"Lowercase, comma-separated, no sentences, no explanations."
        )
        raw_fill = call_ollama("gemma2:2b", prompt_fill)
        extra = [w.strip().lower() for w in raw_fill.split(",") if w.strip()]
        keywords.extend(extra)

    keywords = list(dict.fromkeys(keywords))[:49]
    return keywords


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
