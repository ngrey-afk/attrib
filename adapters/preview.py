import pandas as pd

def show_preview(results: list[dict]):
    """
    Выводит таблицу с результатами:
    File | Title | Description | Keywords (обрезано)
    """
    rows = []
    for r in results:
        rows.append({
            "File": r["file"],
            "Title": r["title"][:50] + ("..." if len(r["title"]) > 50 else ""),
            "Description": r["description"][:80] + ("..." if len(r["description"]) > 80 else ""),
            "Keywords": ", ".join(r["keywords"][:10]) + "..."
        })
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
