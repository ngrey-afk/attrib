from pathlib import Path
import subprocess
import json

from domain.models import MetadataEntity
from services.keyword_service import generate_metadata_with_prompt


def get_caption_with_llava(image_path: Path) -> str:
    """
    Генерируем описание (caption) изображения через Ollama (llava).
    """
    try:
        # Вызываем ollama командой: ollama run llava "Describe this image" -i <image>
        result = subprocess.run(
            ["ollama", "run", "llava", "Describe this image", "-i", str(image_path)],
            capture_output=True,
            text=True,
            check=True
        )
        caption = result.stdout.strip()
        return caption
    except Exception as e:
        print(f"⚠️ Ошибка при генерации caption через llava: {e}")
        return "Unknown image"


def process_image(path: Path) -> MetadataEntity:
    """
    Генерация метаданных для изображения:
    1. Получаем caption через llava.
    2. Передаём caption в LLM для расширенной атрибуции (title, description, keywords).
    """
    caption = get_caption_with_llava(path)

    # Генерация финальных данных через наш сервис
    enriched = generate_metadata_with_prompt(
        caption=caption,
        file_name=path.name,
        media_type="image"
    )

    return MetadataEntity(
        file=str(path),
        title=enriched.get("title", caption.capitalize()),
        description=enriched.get("description", caption),
        keywords=enriched.get("keywords", []),
        disambiguations={},
        category=None,
        secondary_category=None,
        flags={},
        captions=[caption]
    )
