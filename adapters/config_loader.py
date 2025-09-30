import yaml
from pathlib import Path

class Config:
    """Загружает настройки из config.yaml"""

    def __init__(self, path: str = "config.yaml"):
        self._data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))

    @property
    def description_template(self) -> str:
        return self._data["description"]["template"]

    @property
    def description_max_length(self) -> int:
        return self._data["description"]["max_length"]

    @property
    def keywords_total(self) -> int:
        return self._data["keywords"]["total"]

    @property
    def keywords_single(self) -> int:
        return self._data["keywords"]["single_words"]

    @property
    def keywords_double(self) -> int:
        return self._data["keywords"]["two_words"]

    @property
    def keywords_stopwords(self) -> list[str]:
        return self._data["keywords"]["stopwords"]

    @property
    def keywords_mandatory(self) -> list[str]:
        return self._data["keywords"]["mandatory"]

    @property
    def input_dir(self) -> str:
        return self._data["output"]["input_dir"]

    @property
    def output_dir(self) -> str:
        return self._data["output"]["output_dir"]

    @property
    def output_mode(self) -> str:
        return self._data["output"]["mode"]
