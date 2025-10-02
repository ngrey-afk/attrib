from pathlib import Path
from PIL import Image
from domain.models import MetadataEntity
from services.caption_service import generate_caption
from services.keyword_service import generate_metadata_with_prompt


def process_image(path: Path) -> MetadataEntity:
    """
    Генерация метаданных для изображения:
    1. BLIP → Caption
    2. Ollama → Title, Description, Keywords, Category
    """
    caption = generate_caption(str(path))

    enriched = generate_metadata_with_prompt(
        caption=caption,
        file_name=path.name,
        media_type="image"
    )

    return MetadataEntity(
        file=str(path),
        title=enriched.get("title", caption.capitalize()),
        description=enriched.get("description", f"{caption}. High quality stock image"),
        keywords=enriched.get("keywords", []),
        disambiguations={},
        category=enriched.get("category"),
        secondary_category=None,
        flags={},
        captions=[caption]
    )
