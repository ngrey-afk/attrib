from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import torch
import pytesseract

device = "cuda" if torch.cuda.is_available() else "cpu"

# BLIP для описаний
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained(
    "Salesforce/blip-image-captioning-base",
    torch_dtype=torch.float16 if device == "cuda" else torch.float32
).to(device)


def generate_caption(image_path: str) -> str:
    """Создаём caption по картинке (общее описание + распознанный текст)."""
    image = Image.open(image_path).convert("RGB")

    # 1. BLIP описание
    inputs = processor(image, return_tensors="pt").to(device)
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_length=150,
            min_length=20,
            num_beams=5,
            length_penalty=1.0
        )
    caption = processor.decode(output_ids[0], skip_special_tokens=True)

    # 2. OCR (распознаём текст/цифры)
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    custom_config = r'--oem 3 --psm 7 -l eng'
    ocr_text = pytesseract.image_to_string(image, config=custom_config).strip()

    # 3. Объединяем
    if ocr_text:
        return f"{ocr_text}, {caption}"
    return caption
