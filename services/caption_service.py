from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import torch

# Определяем устройство
device = "cuda" if torch.cuda.is_available() else "cpu"

# Загружаем BLIP модель
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained(
    "Salesforce/blip-image-captioning-base",
    torch_dtype=torch.float16 if device == "cuda" else torch.float32
).to(device)


def generate_caption(image_path: str) -> str:
    """
    Генерация детализированного caption для картинки.
    Теперь просим BLIP описывать объект подробно:
    - что изображено
    - основные цвета
    - окружение
    """
    image = Image.open(image_path).convert("RGB")
    inputs = processor(image, return_tensors="pt").to(device)

    # Добавляем инструкцию для более полного описания
    prompt = "Describe this image in detail, including objects, colors, environment, and context."
    input_ids = processor(text=prompt, return_tensors="pt").input_ids.to(device)

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            input_ids=input_ids,
            max_new_tokens=100,   # увеличили лимит для большего описания
            num_beams=5,          # beam search для лучшего качества
            early_stopping=True
        )

    caption = processor.decode(output_ids[0], skip_special_tokens=True)
    return caption.strip()
