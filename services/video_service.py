from pathlib import Path
import subprocess
from domain.models import MetadataEntity
from services.caption_service import generate_caption
from services.keyword_service import generate_metadata_with_prompt
from services.category_service import detect_category

CACHE_DIR = Path(".cache/frames")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def get_video_duration(path: Path) -> float:
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0

def extract_frames(path: Path, num_frames: int = 3) -> list[Path]:
    duration = get_video_duration(path)
    if duration <= 0:
        return []
    timestamps = [duration * i / (num_frames + 1) for i in range(1, num_frames + 1)]
    frame_paths = []
    for idx, ts in enumerate(timestamps, start=1):
        frame_file = CACHE_DIR / f"{path.stem}_frame_{idx}.jpg"
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-ss", str(ts),
                    "-i", str(path),
                    "-frames:v", "1",
                    "-q:v", "2",
                    str(frame_file)
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            if frame_file.exists():
                frame_paths.append(frame_file)
        except Exception as e:
            print(f"⚠️ Ошибка при извлечении кадра {idx}: {e}")
    return frame_paths

def process_video(path: Path) -> MetadataEntity:
    try:
        frames = extract_frames(path, num_frames=1)
        caption = generate_caption(str(frames[0])) if frames else ""
        enriched = generate_metadata_with_prompt(caption, media_type="video")

        return MetadataEntity(
            file=str(path),
            title=enriched.get("title"),
            description=enriched.get("description"),
            keywords=enriched.get("keywords"),
            category=detect_category(enriched.get("keywords", [])),
            flags={"video": True},
            captions=[caption] if caption else [],
            disambiguations=[]
        )
    except Exception as e:
        print(f"❌ Ошибка при обработке видео {path}: {e}")
        return MetadataEntity(file=str(path), title="", description="", keywords=[], disambiguations=[])
