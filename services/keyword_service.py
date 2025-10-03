import subprocess
import re
from services.priority_synonyms import priority_synonyms
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


def generate_keywords(caption: str, media_type: str, description: str = "") -> list[str]:
    stopwords = {
        "a","the","and","with","on","in","of","to","for","by","at","is","are",
        "was","were","this","that","these","those","it","its","an","as","one",
        "here","there","them","those","someone","some","any"
    }

    # --- 1. базовые объекты ---
    words = re.findall(r"\b[a-zA-Z]+\b", caption.lower())
    objects = [w for w in words if w not in stopwords and len(w) > 2]
    base_words = list(dict.fromkeys(objects))[:10]

    # --- 2. приоритетные синонимы ---
    expanded_objects = []
    for obj in base_words:
        expanded_objects.append(obj)
        if obj in priority_synonyms:
            expanded_objects.extend(priority_synonyms[obj])
        if obj in manual_expansions:
            expanded_objects.extend(manual_expansions[obj])

    # --- 3. AI-сгенерированные синонимы ---
    prompt_synonyms = (
        f"Generate synonyms or very close variations for these objects: {', '.join(base_words)}. "
        f"Focus on direct names, plural forms, related nouns (e.g. dog, dogs, puppy, puppies, canine). "
        f"Output lowercase, comma-separated single words, no sentences."
    )
    raw_syn = call_ollama("gemma2:2b", prompt_synonyms)
    synonyms = [w.strip().lower() for w in raw_syn.split(",") if w.strip()] if raw_syn else []

    # --- 4. категории ---
    prompt_themes = (
        f"Extract 5–8 broader categories related to these objects: {', '.join(base_words)}. "
        f"Examples: animals, pets, christmas, decorations, travel, technology. "
        f"Output only lowercase, comma-separated single words. No explanations."
    )
    raw_themes = call_ollama("gemma2:2b", prompt_themes)
    themes = [w.strip().lower() for w in raw_themes.split(",") if w.strip()] if raw_themes else []

    # --- 5. тематические фразы из описания ---
    desc_phrases = []
    if description:
        prompt_desc = (
            f"From this description, extract 5–8 short commercial THEMES (2–3 words): {description}. "
            f"Examples: animal care, veterinary clinic, best friend, holiday celebration. "
            f"Output lowercase, comma-separated, 2–3 words each."
        )
        raw_desc = call_ollama("gemma2:2b", prompt_desc)
        desc_phrases = [w.strip().lower() for w in raw_desc.split(",") if w.strip()] if raw_desc else []

    # --- 6. бизнес-контекст и праздники ---
    prompt_business = (
        f"List 5–8 relevant industries, businesses, or observances for these objects: {', '.join(base_words)}. "
        f"Examples: veterinary, pet care, healthcare, education, christmas, world dog day. "
        f"Output lowercase, comma-separated, max 2 words each. No explanations."
    )
    raw_business = call_ollama("gemma2:2b", prompt_business)
    business_words = [w.strip().lower() for w in raw_business.split(",") if w.strip()] if raw_business else []

    # --- 7. собираем блоки ---
    keywords = []
    keywords += expanded_objects                # главный объект + ручные синонимы
    keywords += synonyms                        # AI-сгенерированные синонимы
    keywords += themes                          # общие категории
    keywords += desc_phrases                    # темы из описания
    keywords += business_words                  # бизнес, праздники

    # --- 8. фильтрация ---
    banned = {"photo", "image", "stock", "photography", "here", "words", "generated"}
    keywords = [w for w in keywords if w not in banned and len(w) > 2]
    keywords = list(dict.fromkeys(keywords))  # уникальные, сохраняя порядок

    # --- 9. добивка до 49 ---
    if len(keywords) < 49:
        prompt_fill = (
            f"Generate {49 - len(keywords)} additional unique related words to these: {', '.join(keywords)}. "
            f"Lowercase, comma-separated, no sentences, no explanations."
        )
        raw_fill = call_ollama("gemma2:2b", prompt_fill)
        extra = [w.strip().lower() for w in raw_fill.split(",") if w.strip()]
        keywords.extend(extra)

    # --- 10. форматирование ---
    single_words = [w for w in keywords if " " not in w][:30]
    phrases = [w for w in keywords if " " in w][:19]
    final_keywords = (single_words + phrases)[:49]

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
