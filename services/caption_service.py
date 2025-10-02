from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained(
    "Salesforce/blip-image-captioning-base",
    torch_dtype=torch.float16 if device == "cuda" else torch.float32
).to(device)

def generate_caption(image_path: str) -> str:
    """Создаём более подробный caption по картинке"""
    image = Image.open(image_path).convert("RGB")
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
    return caption
