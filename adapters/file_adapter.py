from pathlib import Path
from attrib.domain.file_entity import FileEntity

def detect_file_type(path: Path) -> str:
    """Определяем тип файла по расширению"""
    if path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
        return "image"
    elif path.suffix.lower() in [".mp4", ".mov", ".avi"]:
        return "video"
    else:
        return "unknown"

def load_files(input_dir: str) -> list[FileEntity]:
    """Загружаем список файлов для обработки"""
    files = []
    for p in Path(input_dir).iterdir():
        if p.is_file():
            ftype = detect_file_type(p)
            if ftype != "unknown":
                files.append(FileEntity(path=p, file_type=ftype))
    return files
