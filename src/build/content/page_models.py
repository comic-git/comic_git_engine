import os
import posixpath
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


class ImageTitleFallback(str, Enum):
    PAGE_TITLE = "page_title"
    FILENAME = "filename"


class ArchiveEntryMode(str, Enum):
    PAGES = "pages"
    IMAGES = "images"


def normalize_web_path(value: str) -> str:
    return value.replace("\\", "/").strip("/")


def validate_page_asset_path(page_path: str, filename: str, description: str) -> tuple[str, str]:
    normalized = filename.replace("\\", "/")
    pure_path = PurePosixPath(normalized)
    if pure_path.is_absolute() or PureWindowsPath(filename).is_absolute():
        raise ValueError(f"{description.capitalize()} path must be relative to its page folder: {filename}")
    page_root = Path(page_path).resolve()
    candidate = page_root.joinpath(*pure_path.parts).resolve()
    try:
        candidate.relative_to(page_root)
    except ValueError as e:
        raise ValueError(f"{description.capitalize()} path must stay inside its page folder: {filename}") from e
    if not candidate.is_file():
        raise ValueError(f"{description.capitalize()} path must be a file: {filename}")
    return candidate.relative_to(page_root).as_posix(), str(candidate)


def validate_unique_filenames(filenames: list[str]) -> None:
    seen = set()
    for filename in filenames:
        normalized = posixpath.normpath(filename.replace("\\", "/"))
        if normalized in seen:
            raise ValueError(f"Duplicate comic image declaration: {normalized}")
        seen.add(normalized)


def normalize_comic_id(comic_folder: str) -> str:
    return normalize_web_path(comic_folder) or "main"


def build_page_id(comic_folder: str, page_name: str) -> str:
    return f"{normalize_comic_id(comic_folder)}/{normalize_web_path(page_name)}"


def build_image_id(comic_folder: str, page_name: str, filename: str) -> str:
    return f"{build_page_id(comic_folder, page_name)}/{normalize_web_path(filename)}"


def filename_stem(filename: str) -> str:
    return os.path.splitext(PurePosixPath(normalize_web_path(filename)).name)[0]


def resolve_page_title(configured_title: str | None, image_filenames: list[str], page_name: str) -> str:
    if configured_title and configured_title.strip():
        return configured_title
    if image_filenames:
        return filename_stem(image_filenames[0])
    return page_name


def resolve_image_title(
        configured_title: str | None,
        configured_page_title: str | None,
        filename: str,
        fallback: ImageTitleFallback,
) -> str:
    if configured_title is not None:
        return configured_title
    if fallback == ImageTitleFallback.FILENAME:
        return filename_stem(filename)
    if configured_page_title and configured_page_title.strip():
        return configured_page_title
    return filename_stem(filename)


def resolve_image_alt_text(configured_alt_text: str | None, page_alt_text: str | None) -> str:
    if configured_alt_text is not None:
        return configured_alt_text
    return page_alt_text if page_alt_text is not None else ""


def resolve_image_screen_reader_text(
        configured_screen_reader_text: str | None,
        page_screen_reader_text: str | None,
        resolved_alt_text: str,
) -> str:
    if configured_screen_reader_text is not None:
        return configured_screen_reader_text
    if page_screen_reader_text is not None:
        return page_screen_reader_text
    return resolved_alt_text


@dataclass(slots=True)
class ComicImage:
    id: str
    filename: str
    source_path: str
    web_path: str
    title: str
    alt_text: str
    thumbnail_path: str | None = None
    thumbnail_explicit: bool = False
    thumbnail_disabled: bool = False
    screen_reader_text: str | None = None

    def __post_init__(self) -> None:
        if self.screen_reader_text is None:
            self.screen_reader_text = self.alt_text


@dataclass(slots=True)
class ComicPage:
    id: str
    comic_id: str
    comic_folder: str
    page_name: str
    page_dir: str
    url: str
    title: str
    post_date: str
    display_post_date: str
    archive_post_date: str
    images: list[ComicImage]
    thumbnail_path: str | None = None
    thumbnail_explicit: bool = False
    thumbnail_disabled: bool = False
    storyline: str = ""
    characters: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    transcript_languages: list[str] = field(default_factory=list)
    post_md: str = ""
    post_html: str = ""
    transcripts: dict[str, str] = field(default_factory=dict)
    social_media_source: dict[str, Any] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)
    first_id: str = ""
    previous_id: str = ""
    next_id: str = ""
    last_id: str = ""
    first_anchor: str = ""
    previous_anchor: str = ""
    next_anchor: str = ""
    last_anchor: str = ""
    on_comic_click: str = "next comic"


@dataclass(slots=True)
class ArchiveEntry:
    page_id: str
    page_name: str
    page_url: str
    post_date: str
    title: str
    thumbnail_path: str | None
    image: ComicImage | None = None
    image_index: int | None = None
