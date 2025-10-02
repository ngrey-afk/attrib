import subprocess
import base64
import time

def call_ollama_with_image(model: str, prompt: str, image_path: str) -> str:
    """Запуск Ollama vision-модели с картинкой"""
    try:
        # читаем картинку и кодируем в base64
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")

        # JSON-запрос для ollama
        payload = f"""{{
            "prompt": "{prompt}",
            "images": ["{image_b64}"]
        }}"""

        start = time.time()
        result = subprocess.run(
            ["ollama", "run", model],
            input=payload.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        end = time.time()

        output = result.stdout.decode("utf-8").strip()
        return f"\n--- {model} ({end-start:.2f} sec) ---\n{output}\n"

    except subprocess.CalledProcessError as e:
        return f"\n--- {model} ---\n❌ Ошибка: {e.stderr.decode('utf-8')}\n"
    except Exception as e:
        return f"\n--- {model} ---\n❌ Ошибка Python: {e}\n"


if __name__ == "__main__":
    image_path = r"D:\dev\attrib\test_images\01цифры.jpeg"

    models_to_test = [
        "bakllava",  # специализированная для OCR
        "llava:7b",
   #     "moondream"  # лёгкая vision модель
        "granite3.2-vision",            # ещё одна vision модель
        "gemma3:4b",  # vision
    ]

    prompt = "Describe this image and include any visible text or numbers."

    print(f"🖼️ Testing models on: {image_path}\nPROMPT: {prompt}\n")

    for model in models_to_test:
        print(call_ollama_with_image(model, prompt, image_path))
