import re
from configparser import RawConfigParser
from typing import Any, List

from build.content.loaders import load_extra_comic_info as load_extra_comic_info_with_precedence
from build.content.page_models import ArchiveEntryMode, ImageTitleFallback
from core import utils
from core.utils import web_path


def get_links_list(comic_info: RawConfigParser) -> list[dict[str, Any]]:
    link_list = []
    for option in comic_info.options("Links Bar"):
        d = {"name": "", "image_url": ""}
        url = comic_info.get("Links Bar", option)
        if url.startswith("^"):
            d["open_in_new_tab"] = True
            url = url[1:]
        else:
            d["open_in_new_tab"] = False
        d["url"] = web_path(url)
        if re.search(r"\.(jpg|jpeg|png|tif|tiff|gif|bmp|webp|webv|svg|eps)$", option):
            if option.startswith("/"):
                d["image_url"] = web_path(option)
            else:
                d["image_url"] = "https://" + option
        else:
            d["name"] = option
        link_list.append(d)
    return link_list


def get_pages_list(comic_info: RawConfigParser, section_name="Pages"):
    if comic_info.has_section("Pages"):
        return [{"template_name": option, "title": comic_info.get(section_name, option)}
                for option in comic_info.options(section_name)]
    return []


def is_page_configured(comic_info: RawConfigParser, template_name: str) -> bool:
    return any(
        page["template_name"].casefold() == template_name.casefold()
        for page in get_pages_list(comic_info)
    )


def get_extra_comics_list(comic_info: RawConfigParser) -> List[str]:
    return utils.str_to_list(comic_info.get("Comic Settings", "Extra comics", fallback=""))


def get_extra_comic_info(folder_name: str, comic_info: RawConfigParser):
    return load_extra_comic_info_with_precedence(folder_name, comic_info)


def get_archive_entry_mode(comic_info: RawConfigParser) -> ArchiveEntryMode:
    value = comic_info.get("Archive", "Entry mode", fallback="Pages").strip().lower().replace("_", " ")
    if value == "pages":
        return ArchiveEntryMode.PAGES
    if value == "images":
        return ArchiveEntryMode.IMAGES
    raise ValueError("Invalid [Archive] Entry mode. Expected 'Pages' or 'Images'.")


def get_show_text_only_posts(comic_info: RawConfigParser) -> bool:
    return comic_info.getboolean("Archive", "Show text-only posts", fallback=True)


def get_image_title_fallback(comic_info: RawConfigParser) -> ImageTitleFallback:
    value = comic_info.get("Archive", "Image title fallback", fallback="Page title")
    value = value.strip().lower().replace("_", " ")
    if value == "page title":
        return ImageTitleFallback.PAGE_TITLE
    if value == "filename":
        return ImageTitleFallback.FILENAME
    raise ValueError(
        "Invalid [Archive] Image title fallback. Expected 'Page title' or 'Filename'."
    )
