import subprocess
from pathlib import Path
from domain.models import MetadataEntity


def write_image_metadata(path: Path, meta: MetadataEntity):
    """
    Записываем title/description/keywords внутрь изображения (JPG/PNG).
    Используем exiftool, поэтому он должен быть установлен в системе.
    """
    try:
        subprocess.run([
            "exiftool",
            f"-Title={meta.title}",
            f"-Description={meta.description}",
            f"-Keywords={','.join(meta.keywords)}",
            "-overwrite_original",
            str(path)
        ], check=True)
        print(f"✅ Метаданные записаны в {path.name}")
    except Exception as e:
        print(f"❌ Ошибка записи метаданных в {path.name}: {e}")


def write_video_metadata(path: Path, meta: MetadataEntity):
    """
    Для видео создаём .xmp рядом (Shutterstock, Adobe читают такие файлы).
    """
    xmp_path = path.with_suffix(".xmp")
    try:
        with open(xmp_path, "w", encoding="utf-8") as f:
            f.write(f"""<x:xmpmeta xmlns:x="adobe:ns:meta/">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description xmlns:dc="http://purl.org/dc/elements/1.1/">
   <dc:title><rdf:Alt><rdf:li xml:lang="x-default">{meta.title}</rdf:li></rdf:Alt></dc:title>
   <dc:description><rdf:Alt><rdf:li xml:lang="x-default">{meta.description}</rdf:li></rdf:Alt></dc:description>
   <dc:subject><rdf:Bag>{"".join([f"<rdf:li>{kw}</rdf:li>" for kw in meta.keywords])}</rdf:Bag></dc:subject>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>""")
        print(f"✅ XMP сохранён для {path.name}")
    except Exception as e:
        print(f"❌ Ошибка записи XMP для {path.name}: {e}")
    return xmp_path
