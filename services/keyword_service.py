import subprocess
import json
from pathlib import Path
from domain.models import MetadataEntity
from services.prompt_service import load_prompt


def generate_metadata_with_prompt(caption: str, file_name: str, media_type: str) -> dict:
    """
    Отправляем caption + расширенный промпт в Ollama.
    Возвращает JSON с title, description, keywords.
    """
    prompt_text = load_prompt()

    # Финальный запрос
    task = f"""{prompt_text}

File: {file_name}
Type: {media_type}
Caption: {caption}

Return valid JSON with keys: "title", "description", "keywords".
"""

    try:
        result = subprocess.run(
            ["ollama", "run", "mistral"],
            input=task.encode("utf-8"),
            capture_output=True,
            check=True
        )
        output = result.stdout.decode("utf-8").strip()

        # Пытаемся достать JSON
        start = output.find("{")
        end = output.rfind("}") + 1
        if start != -1 and end != -1:
            parsed = json.loads(output[start:end])

            # ⚡ Проверяем и подчищаем
            title = parsed.get("title", caption[:80].capitalize())
            description = parsed.get("description", caption)
            keywords = parsed.get("keywords", [])

            # Случай, если Ollama выдала ключи с запятыми внутри строки
            if isinstance(keywords, str):
                keywords = [kw.strip() for kw in keywords.split(",") if kw.strip()]

            # Ограничение до 49, без повторов
            keywords = list(dict.fromkeys(keywords))[:49]

            return {
                "title": title,
                "description": description,
                "keywords": keywords
            }

        else:
            print(f"⚠️ Не удалось извлечь JSON, ответ: {output}")
            return {"title": caption[:80], "description": caption, "keywords": []}

    except Exception as e:
        print(f"❌ Ошибка генерации атрибуции: {e}")
        return {"title": caption[:80], "description": caption, "keywords": []}
