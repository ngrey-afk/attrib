from pathlib import Path
import subprocess
import tempfile
from domain.models import MetadataEntity
from services.caption_service import generate_caption
from services.keyword_service import generate_metadata_with_prompt
from PIL import Image


def get_video_duration(path: Path) -> float:
    """Определяем длину видео через ffprobe"""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path.resolve())
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True
        )
        return float(result.stdout.decode().strip())
    except Exception as e:
        print(f"❌ Ошибка при получении длительности видео {path}: {e}")
        return 0.0


def extract_frames(path: Path, num_frames: int) -> list[Path]:
    """Извлекаем равномерные кадры"""
    duration = get_video_duration(path)
    if duration <= 0:
        return []

    step = duration / (num_frames + 1)
    temp_dir = Path(tempfile.mkdtemp())
    frame_paths = []

    for i in range(1, num_frames + 1):
        timestamp = i * step
        frame_path = temp_dir / f"frame_{i}.jpg"
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-ss", str(timestamp),
                    "-i", str(path.resolve()),
                    "-frames:v", "1",
                    "-q:v", "2",
                    str(frame_path)
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            frame_paths.append(frame_path)
        except Exception as e:
            print(f"⚠️ Ошибка извлечения кадра {i} из {path}: {e}")

    return frame_paths


def generate_video_captions(path: Path) -> list[str]:
    """Генерация caption’ов по кадрам видео"""
    duration = get_video_duration(path)
    if duration <= 0:
        return []

    num_frames = 3 if duration <= 10 else 5
    frames = extract_frames(path, num_frames)
    captions = []
    for f in frames:
        try:
            captions.append(generate_caption(str(f)))
        except Exception as e:
            print(f"⚠️ Ошибка генерации caption для кадра {f}: {e}")
    return captions


def build_video_description(captions: list[str], max_length: int = 200) -> str:
    """Строим связное описание из caption’ов"""
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
    1. BLIP → captions
    2. Собираем draft description
    3. Ollama → Title, Description, Keywords, Category
    """
    try:
        captions = generate_video_captions(path)
        description = build_video_description(captions)

        llm_result = generate_metadata_with_prompt(
            caption=description,
            file_name=path.name,
            media_type="video"
        )

        return MetadataEntity(
            file=str(path.resolve()),
            title=llm_result.get("title", path.stem),
            description=llm_result.get("description", description),
            keywords=llm_result.get("keywords", []),
            disambiguations={},
            category=llm_result.get("category"),
            secondary_category=None,
            flags={},
            captions=captions
        )
    except Exception as e:
        print(f"❌ Ошибка обработки видео {path}: {e}")
        return MetadataEntity(
            file=str(path.resolve()),
            title=path.stem,
            description="",
            keywords=[],
            disambiguations={},
            category=None,
            secondary_category=None,
            flags={},
            captions=[]
        )
