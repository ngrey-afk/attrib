import subprocess
import time


def call_ollama(model: str, prompt: str) -> str:
    """Запуск Ollama модели и возврат ответа"""
    try:
        start = time.time()
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        end = time.time()
        output = result.stdout.decode("utf-8").strip()
        return f"\n--- {model} ({end - start:.2f} sec) ---\n{output}\n"
    except subprocess.CalledProcessError as e:
        return f"\n--- {model} ---\n❌ Ошибка: {e.stderr.decode('utf-8')}\n"


def test_ai_models(models: list[str], prompt: str):
    print(f"📝 PROMPT:\n{prompt}\n")
    for model in models:
        # запускаем модель и сразу ждём её завершения
        response = call_ollama(model, prompt)
        print(response)

        # выгружаем модель после ответа, чтобы освободить память
        subprocess.run(["ollama", "stop", model], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    models_to_test = [
        "qwen:7b",
        "phi3:mini",
        "llama3",
        "tinyllama",
        "gemma2:2b"
    ]

    prompt = (
        "You are generating an English description for photo/video metadata. "
        "Start exactly with this caption, unchanged: Three little kittens sitting on white bed at home. "
        "After it, continue in a short list style: 3–5 key themes separated by commas. "
        "Focus on subject, setting, and commercial use (e.g. pet care, veterinarian, medical). "
        "Optionally add 1–2 real international or thematic observances (e.g. World Dog Day, International Friendship Day), "
        "only if they clearly match the caption. "
        "Do not use generic words like 'holiday' or 'festival'. "
        "Do not add filler text, do not write full sentences, no introductions, no quotes. "
        "Forbidden: 'concept for', 'ideal for', 'perfect for', 'showcasing'. "
        "Output must be only the description, no comments, no explanations. "
        "Remove articles 'a', 'the'. "
        "Max 200 characters."
    )

    test_ai_models(models_to_test, prompt)
