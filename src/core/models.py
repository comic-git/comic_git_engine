from configparser import RawConfigParser
from dataclasses import dataclass
from typing import Any

from build.content.page_models import ComicPage


@dataclass(slots=True)
class ComicBuildResult:
    comic_folder: str
    comic_info: RawConfigParser
    pages: list[ComicPage]
    global_values: dict[str, Any]
