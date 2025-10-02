from pathlib import Path
from domain.models import MetadataEntity
from services.caption_service import generate_caption
from services.keyword_service import generate_metadata_with_prompt
from services.category_service import detect_category


def process_image(path: Path, callback=None) -> MetadataEntity:
    """Обработка изображения: caption → metadata → category/flags"""
    try:
        caption = generate_caption(str(path))
        if callback and caption:
            callback("captions", caption)

        enriched = generate_metadata_with_prompt(
            caption,
            media_type="image",
            callback=callback
        )

        category = detect_category(enriched.get("keywords", []))
        if callback and category:
            callback("category", category)

        flags = {"image": True}
        if callback:
            callback("flags", str(flags))

        return MetadataEntity(
            file=str(path),
            title=enriched.get("title"),
            description=enriched.get("description"),
            keywords=enriched.get("keywords"),
            category=category,
            flags=flags,
            captions=[caption] if caption else [],
            disambiguations=[]
        )
    except Exception as e:
        print(f"❌ Ошибка при обработке изображения {path}: {e}")
        return MetadataEntity(file=str(path), title="", description="", keywords=[], disambiguations=[])
