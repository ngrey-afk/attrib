import queue
import threading
from pathlib import Path
from typing import Callable

from services.image_service import process_image
from services.video_service import process_video
from domain.models import MetadataEntity

class TaskQueue:
    """Очередь задач атрибуции (последовательная работа с Ollama)."""

    def __init__(self):
        self.queue = queue.Queue()
        self.results: list[MetadataEntity] = []
        self._worker_thread: threading.Thread | None = None
        self._running = False

    def add_task(self, index: int, path: Path):
        """Добавляем задачу в очередь."""
        self.queue.put((index, path))

    def start(self, callback: Callable[[int, str, MetadataEntity], None]):
        """
        Запускаем воркер.
        :param callback: функция для обновления GUI (row, filename, meta).
        """
        if self._running:
            return
        self._running = True

        def worker():
            while not self.queue.empty():
                i, f = self.queue.get()
                try:
                    if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                        meta = process_image(f)
                    elif f.suffix.lower() in [".mp4", ".mov", ".avi", ".mkv"]:
                        meta = process_video(f)
                    else:
                        continue
                except Exception as e:
                    print(f"❌ Ошибка при обработке {f.name}: {e}")
                    continue

                self.results.append(meta)
                callback(i, f.name, meta)

            self._running = False

        self._worker_thread = threading.Thread(target=worker, daemon=True)
        self._worker_thread.start()
