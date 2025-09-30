from typing import List, Protocol

class BaseExporter(Protocol):
    def export(self, results: List[dict], path: str) -> None:
        """Экспортирует results в нужный формат"""
        ...