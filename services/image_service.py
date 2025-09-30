from pathlib import Path
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

from domain.models import MetadataEntity
from services.keyword_service import generate_metadata_with_prompt

# Загружаем BLIP модель один раз
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")


def process_image(path: Path) -> MetadataEntity:
    """
    Генерация метаданных для изображения.
    1. Получаем caption через BLIP.
    2. Отправляем caption в LLM с расширенным промптом → получаем title, description, keywords.
    """
    image = Image.open(path).convert("RGB")
    inputs = processor(image, return_tensors="pt")
    output_ids = model.generate(**inputs, max_new_tokens=50)
    caption = processor.decode(output_ids[0], skip_special_tokens=True, clean_up_tokenization_spaces=False)

    # Генерация финальных данных через LLM
    enriched = generate_metadata_with_prompt(
        prompt="Generate metadata for stock image",
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
        category=None,
        secondary_category=None,
        flags={},
        captions=[caption]
    )
