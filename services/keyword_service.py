from pathlib import Path
import subprocess
import re
from services.category_service import detect_category

def load_prompt() -> str:
    prompt_file = Path("prompts/prompt_en.txt")
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")
    return (
        "You are a bot that helps me describe images and videos (in English) for stock websites. "
        "Return strictly in format:\n"
        "Title: ...\nDescription: ...\nKeywords: ...\n"
    )

def run_ollama(prompt: str) -> str:
    try:
        result = subprocess.run(
            ["ollama", "run", "mistral"],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return result.stdout.decode("utf-8").strip()
    except Exception as e:
        print(f"❌ Ошибка Ollama: {e}")
        return ""

def generate_metadata_with_prompt(caption: str, file_name: str, media_type: str = "image") -> dict:
    base_prompt = load_prompt()

    task = (
        f"{base_prompt}\n\n"
        f"Media type: {media_type}\n"
        f"File name: {file_name}\n"
        f"Caption: {caption}\n\n"
        f"Return strictly in format:\n"
        f"Title: <short title>\n"
        f"Description: <200 chars>\n"
        f"Keywords: <49 comma-separated words>\n"
    )

    output = run_ollama(task)

    title, description, keywords = "", "", []
    try:
        title = re.search(r"Title:\s*(.+)", output, re.IGNORECASE).group(1).strip()
        description = re.search(r"Description:\s*(.+)", output, re.IGNORECASE).group(1).strip()
        raw_keys = re.search(r"Keywords:\s*(.+)", output, re.IGNORECASE | re.DOTALL).group(1).strip()
        keywords = [kw.strip().lower() for kw in raw_keys.split(",") if kw.strip()]
        # гарантируем 49 слов
        keywords = (keywords + ["extra"] * 49)[:49]
    except Exception as e:
        print(f"⚠️ Ошибка парсинга: {e}")

    category = detect_category(keywords)

    return {
        "title": title or file_name,
        "description": description or caption,
        "keywords": keywords,
        "category": category,
    }
