from pathlib import Path
from domain.models import MetadataEntity
from services.caption_service import generate_caption
from services.keyword_service import generate_metadata_with_prompt
from services.category_service import detect_category

def process_image(path: Path) -> MetadataEntity:
    try:
        caption = generate_caption(str(path))
        enriched = generate_metadata_with_prompt(caption, media_type="image")

        return MetadataEntity(
            file=str(path),
            title=enriched.get("title"),
            description=enriched.get("description"),
            keywords=enriched.get("keywords"),
            category=detect_category(enriched.get("keywords", [])),
            flags={"image": True},
            captions=[caption],
            disambiguations=[]
        )
    except Exception as e:
        print(f"❌ Ошибка при обработке изображения {path}: {e}")
        return MetadataEntity(file=str(path), title="", description="", keywords=[], disambiguations=[])
