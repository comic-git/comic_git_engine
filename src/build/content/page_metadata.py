import json
import os
from configparser import RawConfigParser
from typing import Any

from build.content.page_models import ComicImage, ComicPage, normalize_comic_id, normalize_web_path
from core import utils


SCHEMA_VERSION = 1


def build_page_metadata(
        comic_folder: str,
        comic_info: RawConfigParser,
        pages: list[ComicPage],
        scheduled_post_count: int,
        engine_version: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "comic_git_engine_version": engine_version,
        "comic": {
            "id": normalize_comic_id(comic_folder),
            "name": comic_info.get("Comic Info", "Comic name"),
        },
        "scheduled_post_count": scheduled_post_count,
        "pages": [serialize_page(page) for page in pages],
    }


def serialize_page(page: ComicPage) -> dict[str, Any]:
    return {
        "id": page.id,
        "page_name": page.page_name,
        "url": page.url,
        "title": page.title,
        "post_date": page.post_date,
        "thumbnail_url": site_url(page.thumbnail_path),
        "storyline": page.storyline,
        "characters": list(page.characters),
        "tags": list(page.tags),
        "transcript_languages": list(page.transcript_languages),
        "images": [serialize_image(image) for image in page.images],
        "extra": public_extra(page.extra),
    }


def serialize_image(image: ComicImage) -> dict[str, Any]:
    return {
        "filename": image.filename,
        "url": site_url(image.web_path),
        "title": image.title,
        "alt_text": image.alt_text,
        "screen_reader_text": image.screen_reader_text,
        "thumbnail_url": site_url(image.thumbnail_path),
    }


def public_extra(extra: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in extra.items()
        if not key.startswith("!")
    }


def site_url(path: str | None) -> str | None:
    if path is None:
        return None
    base = utils.BASE_DIRECTORY.rstrip("/")
    return f"{base}/{normalize_web_path(path)}"


def save_page_metadata(
        comic_folder: str,
        comic_info: RawConfigParser,
        pages: list[ComicPage],
        scheduled_post_count: int,
        engine_version: str,
) -> str:
    data = build_page_metadata(
        comic_folder,
        comic_info,
        pages,
        scheduled_post_count,
        engine_version,
    )
    output_dir = utils.get_output_dir()
    target_dir = os.path.join(output_dir, f"{comic_folder}comic")
    os.makedirs(target_dir, exist_ok=True)
    path = os.path.join(target_dir, "page_info_list.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    return path
