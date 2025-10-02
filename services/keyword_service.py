import json
import subprocess
import re
from services.prompt_service import load_prompt

def call_ollama(model: str, prompt: str) -> str:
    """Вызов Ollama"""
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

def extract_json_block(text: str) -> str:
    """Ищем JSON-блок {...} даже если вокруг мусор"""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return "{}"

def ensure_extended_title(description: str, current_title: str) -> str:
    """Просим Ollama переписать description как расширенный title, если title слишком короткий"""
    if len(current_title.split()) >= 7:
        return current_title
    prompt = f"Rewrite the following description as an alternative extended title (7–12 words, synonyms, different word order, no repetition):\n\n{description}"
    raw = call_ollama("llama3", prompt)
    return raw.strip().split("\n")[0] if raw else current_title

def expand_keywords(keywords: list[str]) -> list[str]:
    """Гарантируем 49 ключевых слов"""
    unique = list(dict.fromkeys([k.lower().strip() for k in keywords if k.strip()]))
    if len(unique) >= 49:
        return unique[:49]

    prompt = f"Expand the following keywords into exactly 49 unique, lowercase, comma-separated words for stock photo search:\n\n{', '.join(unique)}"
    raw = call_ollama("llama3", prompt)

    new_keywords = []
    if raw:
        if "{" in raw and "}" in raw:  # вдруг JSON
            try:
                data = json.loads(extract_json_block(raw))
                new_keywords = data.get("keywords", [])
            except Exception:
                pass
        if not new_keywords:
            new_keywords = [w.strip() for w in raw.split(",") if w.strip()]

    full_list = list(dict.fromkeys(unique + new_keywords))
    return full_list[:49] if len(full_list) >= 49 else (full_list + ["stock"] * (49 - len(full_list)))

def generate_metadata_with_prompt(caption: str, media_type: str = "image") -> dict:
    """Запрос в Ollama + доработка Title/Keywords"""
    prompt_template = load_prompt()
    full_prompt = f"{prompt_template}\n\nCaption: {caption}\nType: {media_type}"
    raw = call_ollama("llama3", full_prompt)

    json_text = extract_json_block(raw)
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        print("⚠️ Ошибка парсинга Ollama")
        return {"title": "", "description": "", "keywords": []}

    desc = data.get("description", "")
    title = ensure_extended_title(desc, data.get("title", ""))
    keywords = expand_keywords(data.get("keywords", []))

    return {
        "title": title,
        "description": desc,
        "keywords": keywords,
        "category": data.get("category", "")
    }
