import re
from configparser import RawConfigParser
from copy import deepcopy
from typing import Any, List

import core.utils as utils
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


def get_extra_comics_list(comic_info: RawConfigParser) -> List[str]:
    return utils.str_to_list(comic_info.get("Comic Settings", "Extra comics", fallback=""))


def get_extra_comic_info(folder_name: str, comic_info: RawConfigParser):
    comic_info = deepcopy(comic_info)
    del comic_info["Pages"]
    extra_comic_info = RawConfigParser()
    extra_comic_info.read(f"your_content/{folder_name}/comic_info.ini")
    if extra_comic_info.has_section("Links Bar"):
        del comic_info["Links Bar"]
    comic_info.read(f"your_content/{folder_name}/comic_info.ini")
    return comic_info
