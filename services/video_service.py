from pathlib import Path
import subprocess
import tempfile
from domain.models import MetadataEntity
from services.caption_service import generate_caption
from services.keyword_service import generate_metadata_with_prompt


def get_video_duration(path: Path) -> float:
    """Определяем длину видео через ffprobe"""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return float(result.stdout.decode().strip())


def extract_frames(path: Path, num_frames: int) -> list[Path]:
    """Извлекаем равномерные кадры из видео"""
    duration = get_video_duration(path)
    step = duration / (num_frames + 1)

    temp_dir = Path(tempfile.mkdtemp())
    frame_paths = []

    for i in range(1, num_frames + 1):
        timestamp = i * step
        frame_path = temp_dir / f"frame_{i}.jpg"
        subprocess.run([
            "ffmpeg", "-y",
            "-ss", str(timestamp),
            "-i", str(path),
            "-frames:v", "1",
            "-q:v", "2",
            str(frame_path)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        frame_paths.append(frame_path)

    return frame_paths


def generate_video_captions(path: Path) -> list[str]:
    """Генерируем список caption’ов по кадрам"""
    duration = get_video_duration(path)
    num_frames = 3 if duration <= 10 else 5

    frames = extract_frames(path, num_frames)
    captions = [generate_caption(str(f)) for f in frames]
    return captions


def build_video_description(captions: list[str], max_length: int = 200) -> str:
    """Строим связное описание для видео из caption’ов."""
    if not captions:
        return ""

    parts = []
    for i, cap in enumerate(captions):
        if i == 0:
            parts.append(f"A video showing {cap}")
        else:
            parts.append(f"then {cap}")

    description = ", ".join(parts)
    return description[:max_length]


def process_video(path: Path) -> MetadataEntity:
    """
    Полная обработка видео:
    - Извлекаем кадры
    - Генерируем captions
    - Строим описание
    - Прогоняем через LLM для нормализации (prompt_en.txt)
    """
    captions = generate_video_captions(path)
    description = build_video_description(captions)

    llm_result = generate_metadata_with_prompt(
        prompt="Generate metadata for stock video",
        caption=description,
        file_name=path.name,
        media_type="video"
    )

    return MetadataEntity(
        file=str(path),
        title=llm_result.get("title", path.stem),
        description=llm_result.get("description", description),
        keywords=llm_result.get("keywords", []),
        disambiguations={},
        category=None,
        secondary_category=None,
        flags={},
        captions=captions
    )
