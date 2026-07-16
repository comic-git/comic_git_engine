import tomllib
from configparser import RawConfigParser
from typing import Any


STRING_OPTIONS = {
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
    ("image_processing", "thumbnail_size"): ("Image Reprocessing", "Thumbnail size"),
    ("analytics", "google_analytics_id"): ("Google Analytics", "Tracking ID"),
    ("rss", "language"): ("RSS Feed", "Language"),
    ("rss", "image"): ("RSS Feed", "Image"),
    ("rss", "image_width"): ("RSS Feed", "Image width"),
    ("rss", "image_height"): ("RSS Feed", "Image height"),
    ("rss", "title_format"): ("RSS Feed", "RSS title format"),
    ("rss", "channel_description"): ("RSS Feed", "Channel description"),
    ("webring", "endpoint"): ("Webring", "Endpoint"),
    ("webring", "id"): ("Webring", "Webring ID"),
}

BOOL_OPTIONS = {
    ("site", "allow_missing_variables_in_templates"): ("Comic Settings", "Allow missing variables in templates"),
    ("archive", "use_thumbnails"): ("Archive", "Use thumbnails"),
    ("archive", "show_uncategorized_comics"): ("Archive", "Show Uncategorized comics"),
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


def load_comic_config_from_toml(path: str) -> RawConfigParser:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return comic_config_data_to_legacy_parser(data)


def comic_config_data_to_legacy_parser(data: dict[str, Any]) -> RawConfigParser:
    if not isinstance(data, dict):
        raise ValueError("Expected comic_info.toml to contain TOML tables")
    parser = RawConfigParser()
    parser.optionxform = str
    apply_scalar_options(parser, data)
    apply_bool_options(parser, data)
    apply_list_options(parser, data)
    apply_links(parser, data)
    apply_pages(parser, data)
    return parser


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
