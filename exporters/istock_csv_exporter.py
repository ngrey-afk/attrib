import csv
from typing import List

def export_csv_for_istock(results: List[dict], path: str):
    """
    Экспорт для iStock (DeepMeta).
    Исключаем AI-файлы (iStock не принимает).
    Добавляем SeriesID в конце.
    """
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "file name", "created date", "title", "description",
            "country", "brief code", "keywords", "poster timecode",
            "disambiguations", "category", "secondary_category", "flags", "SeriesID"
        ])

        for r in results:
            if r.get("flags", {}).get("ai_generated"):  # ❌ iStock не принимает AI
                continue

            filename = r["file"].split("/")[-1]
            keywords_str = ", ".join(r["keywords"])
            disambig_str = "; ".join([f"{k}:{v}" for k, v in r.get("disambigs", {}).items()])
            flags_str = ";".join([f"{k}:{int(v)}" for k, v in r.get("flags", {}).items()])

            writer.writerow([
                filename, "", r["title"], r["description"], "", "", keywords_str,
                "00:00:01" if r.get("type") == "video" else "",
                disambig_str, r.get("category") or "", r.get("secondary_category") or "", flags_str,
                r.get("series_id", "")
            ])
