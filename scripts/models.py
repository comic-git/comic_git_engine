from configparser import RawConfigParser
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ComicBuildResult:
    comic_folder: str
    comic_info: RawConfigParser
    comic_data_dicts: list[dict[str, Any]]
    global_values: dict[str, Any]
