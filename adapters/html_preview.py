from pathlib import Path

def save_html_preview(results: list[dict], output_file="output/preview.html"):
    """
    Создаёт HTML-таблицу с миниатюрами и атрибуцией
    """
    rows = []
    for r in results:
        img_tag = f'<img src="{r["file"]}" width="120">' if r["type"] == "image" else f'<video src="{r["file"]}" width="120" controls></video>'
        rows.append(f"""
        <tr>
          <td>{img_tag}</td>
          <td>{r["title"]}</td>
          <td>{r["description"]}</td>
          <td>{", ".join(r["keywords"])}</td>
        </tr>
        """)

    html = f"""
    <html>
    <head>
      <style>
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ccc; padding: 6px; vertical-align: top; }}
        img, video {{ max-height: 100px; }}
      </style>
    </head>
    <body>
      <h2>Preview of Generated Metadata</h2>
      <table>
        <tr><th>Preview</th><th>Title</th><th>Description</th><th>Keywords</th></tr>
        {''.join(rows)}
      </table>
    </body>
    </html>
    """
    Path(output_file).write_text(html, encoding="utf-8")
    print(f"✔ Preview saved: {output_file}")
