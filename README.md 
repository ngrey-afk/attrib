# Attrib Project

Автоматическая атрибутация фото/видео для фотостоков.

## Установка
```bash
git clone ...
cd attrib_project
pip install -r requirements.txt
Установить ExifTool  https://exiftool.org

Запуск
Сложите фото/видео в папку input/.
Настройте правила в config.yaml.

Запустите:
python -m attrib.main

Результат:
фото → метаданные внутри файла
видео → создаётся .xmp рядом

Установить ffmpeg:
Windows → скачать сборку и прописать в PATH  https://ffmpeg.org/download.html
Mac → brew install ffmpeg


Как запускать
Сначала обрабатываешь файлы:
python -m attrib.main
→ создаётся output/results.json

Запускаешь веб-интерфейс:
uvicorn web.server:app --reload

Открываешь в браузере:
http://127.0.0.1:8000

скачать словарь гетти
python -m attrib.vocab.vocab_loader your_file.rdf
https://www.getty.edu/research/tools/vocabularies/obtain/download.html?



если запустить на компе ПОЛИНЫ
1. Установить Homebrew (если его нет)
Homebrew — это «менеджер пакетов» для macOS, без него будет сложно.
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
После установки добавь его в PATH (если терминал подскажет команду echo ... >> ~/.zprofile — сделай).

🔧 2. Установить Python 3.11
Наш проект держится на Python 3.11 (оптимально для библиотек типа transformers, fastapi, pandas).
brew install python@3.11
Проверка версии:
python3.11 --version

🔧 3. Создать виртуальное окружение
Это важно, чтобы проект был изолирован.
cd ~/  # например, кладёшь проект сюда
python3.11 -m venv venv
source venv/bin/activate

🔧 4. Установить зависимости проекта
Предполагаем, что у тебя в папке проекта есть requirements.txt. В нём у нас:
fastapi
uvicorn
jinja2
pandas
rdflib
transformers
torch

Устанавливаем:

pip install --upgrade pip
pip install -r requirements.txt

🔧 5. Скопировать проект
🔧 6. Подготовить папки
mkdir -p input output

🔧 7. Запустить обработку
python -m attrib.main

🔧 8. Запустить веб-админку
uvicorn attrib.web.server:app --reload

Потом открыть в браузере:
👉 http://127.0.0.1:8000


Скачиваешь AAT RDF с сайта Getty:
https://www.getty.edu/research/tools/vocabularies/obtain/download.html

Загружаешь в базу:
python -m attrib.vocab.vocab_loader your_file.rdf