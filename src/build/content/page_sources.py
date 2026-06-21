import json
import os
import re
import tomllib
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from build.content import content_paths, transcripts
from core import utils


@dataclass
class PageSource:
    post_date: str
    images: list[str]
    title: str | None = None
    post_text: str = ""
    alt_text: str | None = None
    storyline: str = ""
    characters: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    transcripts: OrderedDict[str, str] = field(default_factory=OrderedDict)
    social_media: dict[str, Any] = field(default_factory=dict)
    extra: OrderedDict[str, str] = field(default_factory=OrderedDict)


KNOWN_LEGACY_PAGE_FIELDS = {
    "Post date",
    "Title",
    "Alt text",
    "Storyline",
    "Characters",
    "Tags",
    "Filename",
    "Filenames",
}


def load_legacy_page_source(page_path: str, comic_folder: str, comic_info) -> PageSource:
    info_path = content_paths.get_page_info_candidates(page_path)[1]
    page_info = utils.read_info(info_path, to_dict=True)
    page_id = os.path.basename(os.path.normpath(page_path))
    images = extract_legacy_page_images(page_path, page_info)
    social_media_path = content_paths.get_page_social_media_path(page_path)
    return PageSource(
        post_date=legacy_date_to_iso(page_info["Post date"], comic_info.get("Comic Settings", "Date format")),
        title=page_info.get("Title"),
        images=images,
        post_text=load_legacy_page_post_text(page_path),
        alt_text=page_info.get("Alt text"),
        storyline=page_info.get("Storyline", ""),
        characters=utils.str_to_list(page_info.get("Characters", "")),
        tags=utils.str_to_list(page_info.get("Tags", "")),
        transcripts=transcripts.load_transcript_source_texts(comic_folder, comic_info, page_id),
        social_media=load_legacy_page_social_media(social_media_path),
        extra=OrderedDict(
            (key, value)
            for key, value in page_info.items()
            if key not in KNOWN_LEGACY_PAGE_FIELDS and not key.startswith("!")
        ),
    )


def load_page_source_from_toml(path: str) -> PageSource:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return PageSource(
        post_date=require_toml_date_string(data, "post_date"),
        title=get_optional_toml_string(data, "title"),
        images=require_toml_string_list(data, "images"),
        post_text=get_optional_toml_string(data, "post_text") or "",
        alt_text=get_optional_toml_string(data, "alt_text"),
        storyline=get_optional_toml_string(data, "storyline") or "",
        characters=get_optional_toml_string_list(data, "characters"),
        tags=get_optional_toml_string_list(data, "tags"),
        transcripts=OrderedDict(require_toml_string_map(data, "transcripts").items()),
        social_media=require_toml_table(data, "social_media"),
        extra=OrderedDict(require_toml_string_map(data, "extra").items()),
    )


def page_source_to_legacy_page_info(page_source: PageSource, comic_info) -> dict[str, Any]:
    page_info: dict[str, Any] = {
        "Post date": iso_date_to_legacy(page_source.post_date, comic_info.get("Comic Settings", "Date format")),
        "image_file_names": list(page_source.images),
        "_toml_managed": True,
        "_inline_post_text": page_source.post_text,
        "_inline_transcripts": OrderedDict(page_source.transcripts),
        "_social_media": dict(page_source.social_media),
    }
    if page_source.title is not None:
        page_info["Title"] = page_source.title
    if page_source.alt_text is not None:
        page_info["Alt text"] = page_source.alt_text
    if page_source.storyline:
        page_info["Storyline"] = page_source.storyline
    if page_source.characters:
        page_info["Characters"] = list(page_source.characters)
    if page_source.tags:
        page_info["Tags"] = list(page_source.tags)
    page_info.update(page_source.extra)
    return page_info


def serialize_page_source_to_toml(page_source: PageSource) -> str:
    lines = [
        f'post_date = {format_toml_string(page_source.post_date)}',
        f'images = {format_toml_string_list(page_source.images)}',
    ]
    if page_source.title is not None:
        lines.append(f'title = {format_toml_string(page_source.title)}')
    if page_source.alt_text is not None:
        lines.append(f'alt_text = {format_toml_multiline_string(page_source.alt_text)}')
    if page_source.storyline:
        lines.append(f'storyline = {format_toml_string(page_source.storyline)}')
    if page_source.characters:
        lines.append(f'characters = {format_toml_string_list(page_source.characters)}')
    if page_source.tags:
        lines.append(f'tags = {format_toml_string_list(page_source.tags)}')
    if page_source.post_text:
        lines.append(f'post_text = {format_toml_multiline_string(page_source.post_text)}')
    if page_source.transcripts:
        lines.append("")
        lines.append("[transcripts]")
        for language, text in page_source.transcripts.items():
            lines.append(f"{format_toml_key(language)} = {format_toml_multiline_string(text)}")
    if page_source.social_media:
        lines.append("")
        lines.append("[social_media]")
        for key, value in page_source.social_media.items():
            lines.append(f"{format_toml_key(key)} = {format_toml_scalar(value)}")
    if page_source.extra:
        lines.append("")
        lines.append("[extra]")
        for key, value in page_source.extra.items():
            lines.append(f"{format_toml_key(key)} = {format_toml_string(value)}")
    return "\n".join(lines) + "\n"


def extract_legacy_page_images(page_path: str, page_info: dict[str, str]) -> list[str]:
    filenames = page_info.get("Filenames") or page_info.get("Filename", "")
    if filenames:
        return utils.str_to_list(filenames)
    image_files = []
    for filename in os.listdir(page_path):
        if filename.startswith("_"):
            continue
        if re.search(r"\.(jpg|jpeg|png|tif|tiff|gif|bmp|webp|webv|svg|eps)$", filename):
            image_files.append(filename)
    return sorted(image_files)


def load_legacy_page_post_text(page_path: str) -> str:
    post_path = os.path.join(page_path, "post.txt")
    if not os.path.isfile(post_path):
        return ""
    with open(post_path, "rb") as f:
        return f.read().decode("utf-8")


def load_legacy_page_social_media(path: str) -> dict[str, Any]:
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    comic_data = data.get("comic")
    if isinstance(comic_data, dict):
        return comic_data
    if isinstance(data, dict):
        return data
    raise ValueError(f"Unsupported page social-media override shape in {path}")


def legacy_date_to_iso(value: str, date_format: str) -> str:
    return datetime.strptime(value, date_format).date().isoformat()


def iso_date_to_legacy(value: str, date_format: str) -> str:
    return date.fromisoformat(value).strftime(date_format)


def require_toml_string(data: dict[str, Any], key: str) -> str:
    value = data[key]
    if not isinstance(value, str):
        raise ValueError(f"Expected '{key}' to be a string in info.toml")
    return value


def require_toml_date_string(data: dict[str, Any], key: str) -> str:
    value = require_toml_string(data, key)
    try:
        date.fromisoformat(value)
    except ValueError as e:
        raise ValueError(f"Expected '{key}' in info.toml to use YYYY-MM-DD format") from e
    return value


def get_optional_toml_string(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Expected '{key}' to be a string in info.toml")
    return value


def require_toml_string_list(data: dict[str, Any], key: str) -> list[str]:
    value = data[key]
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"Expected '{key}' to be a list of strings in info.toml")
    return value


def get_optional_toml_string_list(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key)
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"Expected '{key}' to be a list of strings in info.toml")
    return value


def require_toml_table(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"Expected '{key}' to be a table in info.toml")
    return value


def require_toml_string_map(data: dict[str, Any], key: str) -> dict[str, str]:
    value = data.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in value.items()):
        raise ValueError(f"Expected '{key}' to be a string-to-string table in info.toml")
    return value


def format_toml_key(key: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_-]+", key):
        return key
    return format_toml_string(key)


def format_toml_scalar(value: Any) -> str:
    if isinstance(value, str):
        return format_toml_string(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    raise ValueError(f"Unsupported TOML scalar value: {value!r}")


def format_toml_string(value: str) -> str:
    return json.dumps(value)


def format_toml_string_list(values: list[str]) -> str:
    return "[" + ", ".join(format_toml_string(value) for value in values) + "]"


def format_toml_multiline_string(value: str) -> str:
    escaped = value.replace('"""', '\\"""')
    return f'"""\\\n{escaped}"""'
