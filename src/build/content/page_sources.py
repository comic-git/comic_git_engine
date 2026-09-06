import json
import os
import re
import tomllib
from collections import OrderedDict
from configparser import RawConfigParser
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from build.content import content_paths, transcripts
from core import utils


@dataclass(slots=True)
class PageImageSource:
    filename: str
    title: str | None = None
    alt_text: str | None = None
    thumbnail: str | None = None
    screen_reader_text: str | None = None


@dataclass(slots=True)
class PageSource:
    post_date: str
    images: list[PageImageSource]
    title: str | None = None
    post_text: str = ""
    alt_text: str | None = None
    thumbnail: str | None = None
    storyline: str = ""
    characters: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    transcripts: OrderedDict[str, str] = field(default_factory=OrderedDict)
    social_media: dict[str, Any] = field(default_factory=dict)
    extra: OrderedDict[str, str] = field(default_factory=OrderedDict)
    screen_reader_text: str | None = None


KNOWN_LEGACY_PAGE_FIELDS = {
    "Post date",
    "Title",
    "Alt text",
    "Screen reader text",
    "Thumbnail",
    "Storyline",
    "Characters",
    "Tags",
    "Filename",
    "Filenames",
}
KNOWN_LEGACY_IMAGE_FIELDS = {
    "Filename",
    "Title",
    "Alt text",
    "Screen reader text",
    "Thumbnail",
}
KNOWN_TOML_PAGE_FIELDS = {
    "post_date",
    "title",
    "images",
    "post_text",
    "alt_text",
    "screen_reader_text",
    "thumbnail",
    "storyline",
    "characters",
    "tags",
    "transcripts",
    "social_media",
    "extra",
}
KNOWN_TOML_IMAGE_FIELDS = {
    "filename",
    "title",
    "alt_text",
    "screen_reader_text",
    "thumbnail",
}
SECTION_LINE = re.compile(r"^\s*\[(?P<section>[^\r\n]+)]\s*(?:[#;].*)?$", re.MULTILINE)
TIME_FORMAT_DIRECTIVE = re.compile(r"%(?:[-_0^#]*)(?:H|I|M|S|f|p|X|c|z|Z)")


def load_legacy_page_source(page_path: str, comic_folder: str, comic_info) -> PageSource:
    info_path = content_paths.get_page_info_candidates(page_path)[1]
    page_info, declared_images = load_legacy_page_ini(info_path)
    page_id = os.path.basename(os.path.normpath(page_path))
    images = declared_images if declared_images is not None else extract_legacy_page_images(page_path, page_info)
    social_media_path = content_paths.get_page_social_media_path(page_path)
    return PageSource(
        post_date=legacy_date_to_iso(page_info["Post date"], comic_info.get("Comic Settings", "Date format")),
        title=page_info.get("Title"),
        images=images,
        post_text=load_legacy_page_post_text(page_path),
        alt_text=page_info.get("Alt text"),
        screen_reader_text=page_info.get("Screen reader text"),
        thumbnail=page_info.get("Thumbnail"),
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


def load_legacy_page_ini(path: str) -> tuple[dict[str, str], list[PageImageSource] | None]:
    with open(path, "rb") as f:
        info_string = f.read().decode("utf-8")

    section_match = SECTION_LINE.search(info_string)
    if section_match is None:
        parser_input = "[Page]\n" + info_string
    else:
        preamble = info_string[:section_match.start()]
        meaningful_preamble = any(
            line.strip() and not line.lstrip().startswith(("#", ";"))
            for line in preamble.splitlines()
        )
        parser_input = "[Page]\n" + info_string if meaningful_preamble else info_string

    parser = RawConfigParser()
    parser.optionxform = str
    try:
        parser.read_string(parser_input, source=path)
    except Exception as e:
        raise ValueError(f"Error parsing page configuration {path}: {e}") from e

    page_info = dict(parser["Page"]) if parser.has_section("Page") else {}
    image_sections = []
    for section in parser.sections():
        if section == "Page":
            continue
        if not section.startswith("Image ") or not section.removeprefix("Image ").strip():
            raise ValueError(
                f"Unsupported section [{section}] in {path}. Use [Page] and [Image <label>] sections."
            )
        image_sections.append(section)

    if image_sections and ("Filename" in page_info or "Filenames" in page_info):
        raise ValueError(
            f"Ambiguous image declarations in {path}: do not combine Filename/Filenames with [Image <label>] sections."
        )
    if not image_sections:
        return page_info, None

    images = []
    for section in image_sections:
        values = dict(parser[section])
        unknown = set(values) - KNOWN_LEGACY_IMAGE_FIELDS
        if unknown:
            key = sorted(unknown)[0]
            raise ValueError(f"Unsupported key [{section}] {key} in {path}")
        if "Filename" not in values or not values["Filename"].strip():
            raise ValueError(f"Missing required Filename in [{section}] in {path}")
        images.append(
            PageImageSource(
                filename=values["Filename"],
                title=values.get("Title"),
                alt_text=values.get("Alt text"),
                screen_reader_text=values.get("Screen reader text"),
                thumbnail=values.get("Thumbnail"),
            )
        )
    return page_info, images


def load_page_source_from_toml(path: str) -> PageSource:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    unknown = set(data) - KNOWN_TOML_PAGE_FIELDS
    if unknown:
        raise ValueError(f"Unsupported key {sorted(unknown)[0]} in info.toml")
    return PageSource(
        post_date=require_toml_post_date(data, "post_date"),
        title=get_optional_toml_string(data, "title"),
        images=require_toml_image_list(data, "images"),
        post_text=get_optional_toml_string(data, "post_text") or "",
        alt_text=get_optional_toml_string(data, "alt_text"),
        screen_reader_text=get_optional_toml_string(data, "screen_reader_text"),
        thumbnail=get_optional_toml_string(data, "thumbnail"),
        storyline=get_optional_toml_string(data, "storyline") or "",
        characters=get_optional_toml_string_list(data, "characters"),
        tags=get_optional_toml_string_list(data, "tags"),
        transcripts=OrderedDict(require_toml_string_map(data, "transcripts").items()),
        social_media=require_toml_table(data, "social_media"),
        extra=OrderedDict(require_toml_string_map(data, "extra").items()),
    )


def serialize_page_source_to_toml(page_source: PageSource) -> str:
    try:
        import tomli_w
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "Writing TOML requires migration-only dependencies. Install them with "
            "`pip install -r requirements_migration.txt`."
        ) from e

    data: OrderedDict[str, Any] = OrderedDict([("post_date", page_source.post_date)])
    if page_source.title is not None:
        data["title"] = page_source.title
    if page_source.alt_text is not None:
        data["alt_text"] = page_source.alt_text
    if page_source.screen_reader_text is not None:
        data["screen_reader_text"] = page_source.screen_reader_text
    if page_source.thumbnail is not None:
        data["thumbnail"] = page_source.thumbnail
    if page_source.storyline:
        data["storyline"] = page_source.storyline
    if page_source.characters:
        data["characters"] = page_source.characters
    if page_source.tags:
        data["tags"] = page_source.tags
    if page_source.post_text:
        data["post_text"] = page_source.post_text
    if page_source.transcripts:
        data["transcripts"] = OrderedDict(page_source.transcripts)
    if page_source.social_media:
        data["social_media"] = dict(page_source.social_media)
    if page_source.extra:
        data["extra"] = OrderedDict(page_source.extra)
    if page_source.images:
        data["images"] = [page_image_source_to_toml_data(image) for image in page_source.images]
    return tomli_w.dumps(data, multiline_strings=True)


def page_image_source_to_toml_data(image: PageImageSource) -> OrderedDict[str, str]:
    data = OrderedDict([("filename", image.filename)])
    if image.title is not None:
        data["title"] = image.title
    if image.alt_text is not None:
        data["alt_text"] = image.alt_text
    if image.screen_reader_text is not None:
        data["screen_reader_text"] = image.screen_reader_text
    if image.thumbnail is not None:
        data["thumbnail"] = image.thumbnail
    return data


def extract_legacy_page_images(page_path: str, page_info: dict[str, str]) -> list[PageImageSource]:
    filenames = page_info.get("Filenames") or page_info.get("Filename", "")
    if filenames:
        return [PageImageSource(filename) for filename in utils.str_to_list(filenames)]
    image_files = []
    for filename in os.listdir(page_path):
        if filename.startswith("_"):
            continue
        if re.search(r"\.(jpg|jpeg|png|tif|tiff|gif|bmp|webp|webv|svg|eps)$", filename):
            image_files.append(filename)
    return [PageImageSource(filename) for filename in sorted(image_files)]


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
    try:
        parsed = datetime.strptime(value, date_format)
    except ValueError as configured_format_error:
        try:
            return normalize_iso_post_date(value)
        except ValueError:
            raise ValueError(
                f"Expected post date to match configured format {date_format!r} "
                "or use an ISO date/datetime"
            ) from configured_format_error
    if TIME_FORMAT_DIRECTIVE.search(date_format) or parsed.time() != datetime.min.time():
        return parsed.isoformat()
    return parsed.date().isoformat()


def iso_date_to_legacy(value: str, date_format: str, tz_info=None) -> str:
    parsed = parse_iso_post_date(value)
    if isinstance(parsed, datetime) and tz_info is not None:
        parsed = post_date_to_datetime(value, tz_info)
    return parsed.strftime(date_format)


def normalize_iso_post_date(value: str) -> str:
    parsed = parse_iso_post_date(value.strip())
    return parsed.isoformat()


def parse_iso_post_date(value: str) -> date | datetime:
    try:
        return date.fromisoformat(value)
    except ValueError:
        try:
            return datetime.fromisoformat(value)
        except ValueError as e:
            raise ValueError("Expected an ISO date or datetime") from e


def post_date_to_datetime(value: str, tz_info) -> datetime:
    parsed = parse_iso_post_date(value)
    if not isinstance(parsed, datetime):
        parsed = datetime.combine(parsed, datetime.min.time())
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return tz_info.localize(parsed, is_dst=None)
    return parsed.astimezone(tz_info)


def require_toml_string(data: dict[str, Any], key: str) -> str:
    value = data[key]
    if not isinstance(value, str):
        raise ValueError(f"Expected '{key}' to be a string in info.toml")
    return value


def require_toml_post_date(data: dict[str, Any], key: str) -> str:
    value = data[key]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        try:
            return normalize_iso_post_date(value)
        except ValueError as e:
            raise ValueError(
                f"Expected '{key}' in info.toml to use an ISO date or datetime"
            ) from e
    raise ValueError(
        f"Expected '{key}' in info.toml to be an ISO date or datetime"
    )


def get_optional_toml_string(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Expected '{key}' to be a string in info.toml")
    return value


def require_toml_image_list(data: dict[str, Any], key: str) -> list[PageImageSource]:
    value = data.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"Expected '{key}' to be an array of tables in info.toml")
    images = []
    for index, item in enumerate(value):
        path = f"{key}[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"Expected '{path}' to be a table in info.toml")
        unknown = set(item) - KNOWN_TOML_IMAGE_FIELDS
        if unknown:
            raise ValueError(f"Unsupported key {path}.{sorted(unknown)[0]} in info.toml")
        filename = item.get("filename")
        if not isinstance(filename, str) or not filename.strip():
            raise ValueError(f"Expected '{path}.filename' to be a non-empty string in info.toml")
        images.append(
            PageImageSource(
                filename=filename,
                title=get_optional_toml_string(item, "title"),
                alt_text=get_optional_toml_string(item, "alt_text"),
                screen_reader_text=get_optional_toml_string(item, "screen_reader_text"),
                thumbnail=get_optional_toml_string(item, "thumbnail"),
            )
        )
    return images


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
