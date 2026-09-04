import json
import tomllib
from collections import OrderedDict
from configparser import RawConfigParser
from typing import Any

from core import utils


STRING_OPTIONS = {
    ("engine", "version"): ("Comic Settings", "Engine version"),
    ("comic", "name"): ("Comic Info", "Comic name"),
    ("comic", "author"): ("Comic Info", "Author"),
    ("comic", "description"): ("Comic Info", "Description"),
    ("site", "theme"): ("Comic Settings", "Theme"),
    ("site", "banner_image"): ("Comic Settings", "Banner image"),
    ("site", "date_format"): ("Comic Settings", "Date format"),
    ("site", "timezone"): ("Comic Settings", "Timezone"),
    ("site", "comic_domain"): ("Comic Settings", "Comic domain"),
    ("site", "comic_subdirectory"): ("Comic Settings", "Comic subdirectory"),
    ("site", "on_comic_click"): ("Comic Settings", "On comic click"),
    ("archive", "date_format"): ("Archive", "Date format"),
    ("archive", "entry_mode"): ("Archive", "Entry mode"),
    ("archive", "image_title_fallback"): ("Archive", "Image title fallback"),
    ("transcripts", "folder"): ("Transcripts", "Transcripts folder"),
    ("transcripts", "default_language"): ("Transcripts", "Default language"),
    ("image_processing", "thumbnail_size"): ("Image Reprocessing", "Thumbnail size"),
    ("analytics", "google_analytics_id"): ("Google Analytics", "Tracking ID"),
    ("rss", "language"): ("RSS Feed", "Language"),
    ("rss", "image"): ("RSS Feed", "Image"),
    ("rss", "image_width"): ("RSS Feed", "Image width"),
    ("rss", "image_height"): ("RSS Feed", "Image height"),
    ("rss", "title_format"): ("RSS Feed", "RSS title format"),
    ("rss", "channel_description"): ("RSS Feed", "Description"),
    ("webring", "endpoint"): ("Webring", "Endpoint"),
    ("webring", "id"): ("Webring", "Webring ID"),
}

BOOL_OPTIONS = {
    ("archive", "use_thumbnails"): ("Archive", "Use thumbnails"),
    ("archive", "show_uncategorized_comics"): ("Archive", "Show Uncategorized comics"),
    ("archive", "show_text_only_posts"): ("Archive", "Show text-only posts"),
    ("navigation", "use_images"): ("Navigation Bar", "Use images"),
    ("navigation", "above_comic"): ("Navigation Bar", "Above comic"),
    ("navigation", "below_comic"): ("Navigation Bar", "Below comic"),
    ("navigation", "below_blurb"): ("Navigation Bar", "Below blurb"),
    ("transcripts", "enabled"): ("Transcripts", "Enable transcripts"),
    ("transcripts", "load_from_comic_folder"): ("Transcripts", "Load transcripts from comic folder"),
    ("image_processing", "create_thumbnails"): ("Image Reprocessing", "Create thumbnails"),
    ("image_processing", "overwrite_existing_images"): ("Image Reprocessing", "Overwrite existing images"),
    ("rss", "build"): ("RSS Feed", "Build RSS feed"),
    ("rss", "newest_first"): ("RSS Feed", "Newest first"),
    ("rss", "combine_with_main"): ("RSS Feed", "Combine with Main RSS Feed"),
    ("webring", "enabled"): ("Webring", "Enable webring"),
    ("webring", "show_all_members"): ("Webring", "Show all members"),
    ("webring", "exclude_own_comic_from_members"): ("Webring", "Exclude own comic from members"),
}

LIST_OPTIONS = {
    ("site", "extra_comics"): ("Comic Settings", "Extra comics"),
    ("site", "markdown_extras"): ("Comic Settings", "Markdown extras"),
}

OPTION_MAPPINGS = (STRING_OPTIONS, BOOL_OPTIONS, LIST_OPTIONS)
SUPPORTED_TABLE_KEYS: dict[str, set[str]] = {}
for option_mapping in OPTION_MAPPINGS:
    for table_name, key in option_mapping:
        SUPPORTED_TABLE_KEYS.setdefault(table_name, set()).add(key)

SUPPORTED_TOP_LEVEL_KEYS = frozenset((*SUPPORTED_TABLE_KEYS, "links", "pages", "legacy"))
SUPPORTED_LINK_KEYS = frozenset(("name", "image_url", "url", "open_in_new_tab"))
SUPPORTED_PAGE_KEYS = frozenset(("template_name", "title"))


def load_comic_config_from_toml(path: str) -> RawConfigParser:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return comic_config_data_to_legacy_parser(data)


def serialize_comic_config_to_toml(comic_info: RawConfigParser) -> str:
    try:
        import tomli_w
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "Writing TOML requires migration-only dependencies. Install them with "
            "`pip install -r requirements_migration.txt`."
        ) from e
    return tomli_w.dumps(legacy_parser_to_comic_config_data(comic_info), multiline_strings=True)


def comic_config_data_to_legacy_parser(data: dict[str, Any]) -> RawConfigParser:
    validate_comic_config_schema(data)
    validate_legacy_collisions(data)
    parser = RawConfigParser()
    parser.optionxform = str
    apply_scalar_options(parser, data)
    apply_bool_options(parser, data)
    apply_list_options(parser, data)
    apply_links(parser, data)
    apply_pages(parser, data)
    apply_legacy_options(parser, data)
    return parser


def validate_comic_config_schema(data: dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise ValueError("Expected comic_info.toml to contain TOML tables")
    reject_unknown_keys(data, SUPPORTED_TOP_LEVEL_KEYS, "")
    for table_name, supported_keys in SUPPORTED_TABLE_KEYS.items():
        if table_name not in data:
            continue
        table = data[table_name]
        if not isinstance(table, dict):
            raise ValueError(f"Expected {table_name} in comic_info.toml to be a table")
        reject_unknown_keys(table, supported_keys, table_name)
    validate_collection_item_keys(data, "links", SUPPORTED_LINK_KEYS)
    validate_collection_item_keys(data, "pages", SUPPORTED_PAGE_KEYS)


def reject_unknown_keys(data: dict[str, Any], supported_keys: set[str] | frozenset[str], path: str) -> None:
    for key in data:
        if key in supported_keys:
            continue
        key_path = f"{path}.{key}" if path else key
        raise ValueError(f"Unsupported key {key_path} in comic_info.toml")


def validate_collection_item_keys(
        data: dict[str, Any],
        collection_name: str,
        supported_keys: frozenset[str],
) -> None:
    collection = data.get(collection_name)
    if not isinstance(collection, list):
        return
    for index, item in enumerate(collection):
        if isinstance(item, dict):
            reject_unknown_keys(item, supported_keys, f"{collection_name}[{index}]")


def validate_legacy_collisions(data: dict[str, Any]) -> None:
    legacy = data.get("legacy")
    if not isinstance(legacy, dict):
        return
    first_class_paths = get_first_class_legacy_paths(data)
    for section, options in legacy.items():
        if not isinstance(section, str) or not isinstance(options, dict):
            continue
        for option in options:
            if not isinstance(option, str):
                continue
            first_class_path = first_class_paths.get((section, option))
            if first_class_path is None:
                continue
            legacy_path = f"legacy[{json.dumps(section)}][{json.dumps(option)}]"
            raise ValueError(
                f"{legacy_path} conflicts with {first_class_path} in comic_info.toml"
            )


def get_first_class_legacy_paths(data: dict[str, Any]) -> dict[tuple[str, str], str]:
    paths: dict[tuple[str, str], str] = {}
    for option_mapping in OPTION_MAPPINGS:
        for (table_name, key), legacy_location in option_mapping.items():
            table = data.get(table_name)
            if isinstance(table, dict) and key in table:
                paths[legacy_location] = f"{table_name}.{key}"

    links = data.get("links")
    if isinstance(links, list):
        for index, link in enumerate(links):
            if isinstance(link, dict):
                paths[("Links Bar", get_link_option(link, index))] = f"links[{index}]"

    pages = data.get("pages")
    if isinstance(pages, list):
        for index, page in enumerate(pages):
            if isinstance(page, dict):
                template_name = get_required_string(page, "template_name", f"pages[{index}]")
                paths[("Pages", template_name)] = f"pages[{index}]"

    return paths


def legacy_parser_to_comic_config_data(comic_info: RawConfigParser) -> OrderedDict[str, Any]:
    data: OrderedDict[str, Any] = OrderedDict()
    handled_options: set[tuple[str, str]] = set()
    write_legacy_scalar_options(comic_info, data, handled_options)
    write_legacy_bool_options(comic_info, data, handled_options)
    write_legacy_list_options(comic_info, data, handled_options)
    write_legacy_links(comic_info, data)
    write_legacy_pages(comic_info, data)
    write_unmapped_legacy_options(comic_info, data, handled_options)
    return data


def apply_scalar_options(parser: RawConfigParser, data: dict[str, Any]) -> None:
    for (table_name, key), (section, option) in STRING_OPTIONS.items():
        if not has_toml_key(data, table_name, key):
            continue
        value = data[table_name][key]
        if not isinstance(value, str):
            raise ValueError(f"Expected {table_name}.{key} in comic_info.toml to be a string")
        set_option(parser, section, option, value)


def apply_bool_options(parser: RawConfigParser, data: dict[str, Any]) -> None:
    for (table_name, key), (section, option) in BOOL_OPTIONS.items():
        if not has_toml_key(data, table_name, key):
            continue
        value = data[table_name][key]
        if not isinstance(value, bool):
            raise ValueError(f"Expected {table_name}.{key} in comic_info.toml to be a boolean")
        set_option(parser, section, option, "true" if value else "false")


def apply_list_options(parser: RawConfigParser, data: dict[str, Any]) -> None:
    for (table_name, key), (section, option) in LIST_OPTIONS.items():
        if not has_toml_key(data, table_name, key):
            continue
        value = data[table_name][key]
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ValueError(f"Expected {table_name}.{key} in comic_info.toml to be a list of strings")
        set_option(parser, section, option, ", ".join(value))


def apply_links(parser: RawConfigParser, data: dict[str, Any]) -> None:
    if "links" not in data:
        return
    links = data["links"]
    if not isinstance(links, list):
        raise ValueError("Expected links in comic_info.toml to be a list of tables")
    ensure_section(parser, "Links Bar")
    for index, link in enumerate(links):
        if not isinstance(link, dict):
            raise ValueError(f"Expected links[{index}] in comic_info.toml to be a table")
        option = get_link_option(link, index)
        url = get_required_string(link, "url", f"links[{index}]")
        open_in_new_tab = get_optional_bool(link, "open_in_new_tab", f"links[{index}]", default=False)
        if open_in_new_tab and not url.startswith("^"):
            url = "^" + url
        parser.set("Links Bar", option, url)


def apply_pages(parser: RawConfigParser, data: dict[str, Any]) -> None:
    if "pages" not in data:
        return
    pages = data["pages"]
    if not isinstance(pages, list):
        raise ValueError("Expected pages in comic_info.toml to be a list of tables")
    ensure_section(parser, "Pages")
    for index, page in enumerate(pages):
        if not isinstance(page, dict):
            raise ValueError(f"Expected pages[{index}] in comic_info.toml to be a table")
        template_name = get_required_string(page, "template_name", f"pages[{index}]")
        title = get_required_string(page, "title", f"pages[{index}]")
        parser.set("Pages", template_name, title)


def apply_legacy_options(parser: RawConfigParser, data: dict[str, Any]) -> None:
    legacy = data.get("legacy")
    if legacy is None:
        return
    if not isinstance(legacy, dict):
        raise ValueError("Expected legacy in comic_info.toml to be a table")
    for section, options in legacy.items():
        if not isinstance(section, str) or not isinstance(options, dict):
            raise ValueError("Expected legacy in comic_info.toml to be a table of section tables")
        ensure_section(parser, section)
        for option, value in options.items():
            if not isinstance(option, str) or not isinstance(value, str):
                raise ValueError(f"Expected legacy.{section} in comic_info.toml to contain string values")
            parser.set(section, option, value)


def write_legacy_scalar_options(
        comic_info: RawConfigParser,
        data: OrderedDict[str, Any],
        handled_options: set[tuple[str, str]],
) -> None:
    for (table_name, key), (section, option) in STRING_OPTIONS.items():
        if not comic_info.has_option(section, option):
            continue
        ensure_toml_table(data, table_name)[key] = comic_info.get(section, option)
        handled_options.add((section, option))


def write_legacy_bool_options(
        comic_info: RawConfigParser,
        data: OrderedDict[str, Any],
        handled_options: set[tuple[str, str]],
) -> None:
    for (table_name, key), (section, option) in BOOL_OPTIONS.items():
        if not comic_info.has_option(section, option):
            continue
        ensure_toml_table(data, table_name)[key] = comic_info.getboolean(section, option)
        handled_options.add((section, option))


def write_legacy_list_options(
        comic_info: RawConfigParser,
        data: OrderedDict[str, Any],
        handled_options: set[tuple[str, str]],
) -> None:
    for (table_name, key), (section, option) in LIST_OPTIONS.items():
        if not comic_info.has_option(section, option):
            continue
        ensure_toml_table(data, table_name)[key] = utils.str_to_list(comic_info.get(section, option))
        handled_options.add((section, option))


def write_legacy_links(comic_info: RawConfigParser, data: OrderedDict[str, Any]) -> None:
    if not comic_info.has_section("Links Bar"):
        return
    links = []
    for option in comic_info.options("Links Bar"):
        url = comic_info.get("Links Bar", option)
        link: OrderedDict[str, Any] = OrderedDict()
        if is_image_link_option(option):
            link["image_url"] = option
        else:
            link["name"] = option
        if url.startswith("^"):
            link["url"] = url[1:]
            link["open_in_new_tab"] = True
        else:
            link["url"] = url
        links.append(link)
    if links:
        data["links"] = links


def write_legacy_pages(comic_info: RawConfigParser, data: OrderedDict[str, Any]) -> None:
    if not comic_info.has_section("Pages"):
        return
    pages = []
    for option in comic_info.options("Pages"):
        pages.append(OrderedDict([
            ("template_name", option),
            ("title", comic_info.get("Pages", option)),
        ]))
    if pages:
        data["pages"] = pages


def write_unmapped_legacy_options(
        comic_info: RawConfigParser,
        data: OrderedDict[str, Any],
        handled_options: set[tuple[str, str]],
) -> None:
    handled_sections = {"Links Bar", "Pages"}
    legacy: OrderedDict[str, OrderedDict[str, str]] = OrderedDict()
    for section in comic_info.sections():
        if section in handled_sections:
            continue
        for option in comic_info.options(section):
            if (section, option) in handled_options:
                continue
            legacy.setdefault(section, OrderedDict())[option] = comic_info.get(section, option)
    if legacy:
        data["legacy"] = legacy


def has_toml_key(data: dict[str, Any], table_name: str, key: str) -> bool:
    if table_name not in data:
        return False
    table = data[table_name]
    if not isinstance(table, dict):
        raise ValueError(f"Expected {table_name} in comic_info.toml to be a table")
    return key in table


def get_link_option(link: dict[str, Any], index: int) -> str:
    has_name = "name" in link
    has_image_url = "image_url" in link
    if has_name == has_image_url:
        raise ValueError(f"Expected links[{index}] in comic_info.toml to define exactly one of name or image_url")
    if has_name:
        return get_required_string(link, "name", f"links[{index}]")
    return get_required_string(link, "image_url", f"links[{index}]")


def get_required_string(data: dict[str, Any], key: str, field_name: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise ValueError(f"Expected {field_name}.{key} in comic_info.toml to be a string")
    return value


def get_optional_bool(data: dict[str, Any], key: str, field_name: str, default: bool) -> bool:
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"Expected {field_name}.{key} in comic_info.toml to be a boolean")
    return value


def set_option(parser: RawConfigParser, section: str, option: str, value: str) -> None:
    ensure_section(parser, section)
    parser.set(section, option, value)


def ensure_section(parser: RawConfigParser, section: str) -> None:
    if not parser.has_section(section):
        parser.add_section(section)


def ensure_toml_table(data: OrderedDict[str, Any], table_name: str) -> OrderedDict[str, Any]:
    if table_name not in data:
        data[table_name] = OrderedDict()
    return data[table_name]


def is_image_link_option(option: str) -> bool:
    return option.lower().endswith(
        (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".gif", ".bmp", ".webp", ".webv", ".svg", ".eps")
    )
