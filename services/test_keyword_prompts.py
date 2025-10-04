import subprocess
import textwrap
import datetime
import re


def call_ollama(model: str, prompt: str, timeout: int = 120) -> str:
    """Вызывает локальную модель Ollama и возвращает строковый ответ."""
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=True
        )
        return result.stdout.decode("utf-8").strip()
    except subprocess.TimeoutExpired:
        print("⚠️ Таймаут генерации, повтор...")
        return ""
    except subprocess.CalledProcessError as e:
        print("❌ Ошибка Ollama:", e.stderr.decode("utf-8"))
        return ""


def clean_keywords(text: str) -> list[str]:
    """Чистим, фильтруем и нормализуем ключевые слова."""
    text = re.sub(r"[#*\-\n\r\.\|]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    words = [w.strip().lower() for w in text.split(",") if w.strip()]
    cleaned = []
    for w in words:
        w = re.sub(r"[^\w\s-]", "", w)
        if 2 <= len(w) <= 50 and w not in cleaned:
            cleaned.append(w)
    return cleaned


def test_prompts():
    caption = "A dog wearing a Santa hat sitting on a sofa near Christmas tree"
    description = (
        "A cute dog with red hat sitting on cozy couch, festive decoration, "
        "Christmas celebration, winter holidays"
    )

    log_path = "ollama_keywords_test.txt"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"🧠 Тест генерации ключевых слов\n{datetime.datetime.now()}\n\n")

    # ЕДИНЫЙ ПРОМПТ
    prompt = f"""
You are generating high-quality English keywords for stock photo/video metadata.

Scene description:
"{caption}"
"{description}"

TASK:
Generate exactly 120 unique English keywords (1–3 words each) optimized for stock photo metadata on Shutterstock and Adobe Stock.
The goal is to create diverse, relevant, and commercially valuable keywords describing both the main subjects and the broader visual/emotional context.

STRUCTURE PRIORITY:
1. Start with 8–10 **commercially strong subjects** (combine object + context):
   Examples: christmas dog, festive dog, dog on sofa, cozy pet, santa hat dog, family home interior.
2. Then add 6–8 **main visual objects and their synonyms**:
   Examples: dog, puppy, pet, santa hat, christmas tree, sofa, cozy couch, living room.
3. Then 6–8 **emotional and lifestyle words**:
   Examples: joy, warmth, love, happiness, family, comfort, peace, togetherness.
4. Add 8–10 **context and atmosphere** terms:
   Examples: winter interior, cozy home, holiday decor, festive background, warm tones, soft lighting.
5. If the image clearly belongs to a holiday or event, include only **those relevant holidays** (e.g., christmas, new year, halloween).
6. Add 10–15 **artistic and technical composition words**:
   Examples: natural light, copy space, minimalist decor, close up, bokeh, texture, detail, warm background.
7. Finally, add 10–15 **short 2–3-word semantic phrases** mixing mood, style, and action:
   Examples: joyful celebration, festive atmosphere, cozy winter home, family holiday moment, creative lifestyle.

RULES:
- Prioritize the most descriptive and commercial keywords first.
- Avoid generic terms like “photo,” “image,” “stock,” or “concept.”
- Avoid repeating the same root more than twice (e.g., “christmas” only 2 times).
- Output only lowercase, comma-separated keywords in one line.
- No lists, numbering, markdown, or explanations.
- Do not invent unrelated holidays.

Output must contain **exactly 120 comma-separated keywords** in one line.



"""

    print("\n=== ТЕСТ: Универсальный промпт ===")
    result = call_ollama("gemma2:2b", prompt)

    if not result:
        print("⚠️ Модель не вернула ответ.")
        return

    keywords = clean_keywords(result)

    if len(keywords) < 50:
        fill_prompt = (
            f"Generate {100 - len(keywords)} additional unique related keywords "
            f"for this topic: {caption}. Lowercase, comma-separated, 1–2 words each."
        )
        extra = call_ollama("gemma2:2b", fill_prompt)
        extra_words = clean_keywords(extra)
        keywords.extend(extra_words)
        keywords = list(dict.fromkeys(keywords))

    print(f"🟢 Получено: {len(keywords)} слов")
    preview = ", ".join(keywords[:20])
    print(preview + " ...")
    print("========================================")

    with open(log_path, "a", encoding="utf-8") as f:
        f.write("=== Универсальный промпт ===\n")
        f.write(f"🟢 Получено: {len(keywords)} слов\n")
        for j in range(0, len(keywords), 5):
            f.write(", ".join(keywords[j:j + 5]) + "\n")
        f.write("========================================\n\n")

    print(f"\n✅ Результаты сохранены в файл: {log_path}")


if __name__ == "__main__":
    print(textwrap.dedent("""
        ───────────────────────────────────────────────
        🧠  Тест генерации ключевых слов через Ollama
        ───────────────────────────────────────────────
    """))
    test_prompts()
