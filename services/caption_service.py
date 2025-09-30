from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image

# Загружаем модель BLIP один раз при импорте
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

def generate_caption(image_path: str) -> str:
    """
    Создаём черновой caption по картинке (одному кадру видео или изображению).
    Используем BLIP для генерации.
    """
    image = Image.open(image_path).convert("RGB")
    inputs = processor(image, return_tensors="pt")
    output_ids = model.generate(**inputs, max_new_tokens=50)  # исправлено
    caption = processor.decode(output_ids[0], skip_special_tokens=True, clean_up_tokenization_spaces=False)
    return caption
