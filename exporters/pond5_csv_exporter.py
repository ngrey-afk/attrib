import csv
from typing import List

def export_csv_for_pond5(results: List[dict], path: str):
    """
    Экспорт для Pond5.
    Принимает любые работы. Добавляем SeriesID.
    """
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Filename", "Title", "Description", "Keywords", "Category",
            "Secondary Category", "Model Release", "Property Release", "Price", "SeriesID"
        ])

        for r in results:
            keywords_str = ", ".join(r["keywords"])
            writer.writerow([
                r["file"].split("/")[-1], r["title"], r["description"],
                keywords_str, r.get("category") or "", r.get("secondary_category") or "",
                "", "", "", r.get("series_id", "")
            ])
