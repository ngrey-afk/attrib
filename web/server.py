from fastapi import FastAPI, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from pathlib import Path
import json, asyncio

app = FastAPI(
    title="Attrib Web API",
    description="Веб-интерфейс для атрибуции фото и видео (Shutterstock, Adobe, iStock, Pond5)",
    version="1.0.0"
)

# Пути
RESULTS_FILE = Path("output/results.json")
templates_dir = Path(__file__).parent / "templates"
env = Environment(loader=FileSystemLoader(templates_dir))

# Директории для статических файлов
app.mount("/files", StaticFiles(directory="input"), name="files")
app.mount("/output", StaticFiles(directory="output"), name="output")


# --- Вспомогательные методы ---
def load_results():
    if RESULTS_FILE.exists():
        return json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
    return []


def save_results(results):
    RESULTS_FILE.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


# --- Эндпоинты ---
@app.get("/", response_class=HTMLResponse)
def index(q: str = Query(None)):
    """Главная страница: просмотр и поиск атрибуции"""
    results = load_results()
    if q:
        q_lower = q.lower()
        results = [
            r for r in results
            if q_lower in r["file"].lower()
            or q_lower in r["description"].lower()
            or any(q_lower in kw for kw in r["keywords"])
            or any(q_lower in k for k in (r.get("disambigs") or {}))
        ]

    try:
        template = env.get_template("preview.html")
        return template.render(results=results, query=q or "")
    except TemplateNotFound:
        return HTMLResponse("<h2>❌ Шаблон preview.html не найден</h2>", status_code=500)


@app.post("/update")
def update(file: str = Form(...), title: str = Form(...), description: str = Form(...),
           keywords: str = Form(...), category: str = Form(""),
           ai_generated: str = Form(None), fictional: str = Form(None), people_not_real: str = Form(None)):
    """Обновление атрибутов одного файла"""
    results = load_results()
    for r in results:
        if r["file"] == file:
            r["title"] = title.strip()
            r["description"] = description.strip()
            r["keywords"] = [kw.strip() for kw in keywords.split(",") if kw.strip()]
            r["category"] = category.strip() or None
            r["flags"] = {
                "ai_generated": ai_generated is not None,
                "fictional": fictional is not None,
                "people_not_real": people_not_real is not None
            }
            break
    save_results(results)
    return RedirectResponse("/", status_code=303)


@app.post("/batch_update")
def batch_update(files: str = Form(...), category: str = Form(""),
                 ai_generated: str = Form(None), fictional: str = Form(None), people_not_real: str = Form(None)):
    """Пакетное обновление атрибутов сразу для нескольких файлов"""
    file_list = [f.strip() for f in files.split(",") if f.strip()]
    results = load_results()
    for r in results:
        if r["file"] in file_list:
            if category:
                r["category"] = category.strip()
            if any([ai_generated, fictional, people_not_real]):
                r["flags"] = {
                    "ai_generated": ai_generated is not None,
                    "fictional": fictional is not None,
                    "people_not_real": people_not_real is not None
                }
    save_results(results)
    return RedirectResponse("/", status_code=303)


# --- WebSocket автообновления ---
last_mtime = 0

@app.websocket("/ws")
async def websocket_endpoint(ws):
    """Сообщает фронту, если изменился results.json"""
    await ws.accept()
    global last_mtime
    while True:
        await asyncio.sleep(2)
        if RESULTS_FILE.exists():
            mtime = RESULTS_FILE.stat().st_mtime
            if mtime != last_mtime:
                last_mtime = mtime
                await ws.send_text("refresh")


# --- Системные маршруты ---
@app.get("/health")
def health():
    """Проверка работоспособности"""
    return {"status": "ok"}


@app.get("/results", response_class=JSONResponse)
def get_results():
    """Отдать JSON прямо в браузер"""
    return load_results()
