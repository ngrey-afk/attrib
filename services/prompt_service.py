"""
Сервис загрузки и построения промптов для LLM.
"""
from pathlib import Path

def load_prompt(prompt_path: str = "prompts/prompt_en.txt") -> str:
    """Загружаем расширенный промпт из файла"""
    prompt_file = Path(prompt_path)
    if prompt_file.exists():
        text = prompt_file.read_text(encoding="utf-8").strip()
        print(f"✅ Загружен кастомный промпт из {prompt_file}")
        return text
    print("⚠️ prompt_en.txt не найден, используем дефолтный")
    return "You are a metadata generator"
