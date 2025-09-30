import csv
from typing import List

def export_csv_for_adobe(results: List[dict], path: str):
    """
    Экспорт для Adobe Stock.
    Adobe принимает AI. Добавляем SeriesID.
    """
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Filename", "Title", "Description", "Keywords", "Category", "Flags", "SeriesID"])

        for r in results:
            keywords_str = ", ".join(r["keywords"])
            flags_str = ";".join([f"{k}:{int(v)}" for k, v in r.get("flags", {}).items()])

            writer.writerow([
                r["file"].split("/")[-1], r["title"], r["description"],
                keywords_str, r.get("category") or "", flags_str, r.get("series_id", "")
            ])
