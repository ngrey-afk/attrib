import csv
from typing import List

def export_csv_for_shutterstock(results: List[dict], path: str):
    """
    Экспорт для Shutterstock.
    Исключаем AI-файлы (Shutterstock не принимает).
    Добавляем SeriesID.
    """
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Filename", "Title", "Description", "Keywords", "Category", "SeriesID"])

        for r in results:
            if r.get("flags", {}).get("ai_generated"):  # ❌ Shutterstock не принимает AI
                continue

            keywords_str = ", ".join(r["keywords"])
            writer.writerow([
                r["file"].split("/")[-1], r["title"], r["description"],
                keywords_str, r.get("category") or "", r.get("series_id", "")
            ])
