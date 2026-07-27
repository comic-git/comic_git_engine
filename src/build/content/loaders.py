import os
from configparser import RawConfigParser
from copy import deepcopy

from build.content import content_paths
from build.content.comic_config_sources import load_comic_config_from_toml
from build.content.page_sources import (
    PageSource,
    load_legacy_page_source,
    load_page_source_from_toml,
)
from core import utils


NOT_FOUND = object()


def load_main_comic_info() -> RawConfigParser:
    toml_path, legacy_path = content_paths.get_main_comic_info_candidates()
    if os.path.isfile(toml_path):
        comic_info = load_main_comic_info_toml(toml_path)
        if comic_info is not NOT_FOUND:
            return comic_info
    return load_legacy_comic_info(legacy_path)


def load_main_comic_info_toml(path: str) -> RawConfigParser | object:
    return load_comic_config_from_toml(path)


def load_extra_comic_info(folder_name: str, comic_info: RawConfigParser) -> RawConfigParser:
    toml_path, legacy_path = content_paths.get_extra_comic_info_candidates(folder_name)
    if os.path.isfile(toml_path):
        extra_comic_info = load_extra_comic_info_toml(folder_name, comic_info, toml_path)
        if extra_comic_info is not NOT_FOUND:
            return extra_comic_info
    return load_legacy_extra_comic_info(legacy_path, comic_info)


def load_extra_comic_info_toml(_folder_name: str, comic_info: RawConfigParser, path: str) -> RawConfigParser | object:
    extra_comic_info = load_comic_config_from_toml(path)
    return merge_extra_comic_info(extra_comic_info, comic_info)


def load_page_source(
        page_path: str,
        comic_folder: str,
        comic_info: RawConfigParser,
) -> tuple[str | None, PageSource | None]:
    toml_path, legacy_path = content_paths.get_page_info_candidates(page_path)
    if os.path.isfile(toml_path):
        return toml_path, load_page_source_from_toml(toml_path)
    if os.path.isfile(legacy_path):
        return legacy_path, load_legacy_page_source(page_path, comic_folder, comic_info)
    return None, None


def load_legacy_comic_info(path: str) -> RawConfigParser:
    return utils.read_info(path)


def load_legacy_extra_comic_info(path: str, comic_info: RawConfigParser) -> RawConfigParser:
    merged_info = deepcopy(comic_info)
    if merged_info.has_section("Pages"):
        del merged_info["Pages"]
    extra_comic_info = RawConfigParser()
    extra_comic_info.read(path)
    if extra_comic_info.has_section("Links Bar") and merged_info.has_section("Links Bar"):
        del merged_info["Links Bar"]
    merged_info.read(path)
    return merged_info


def merge_extra_comic_info(extra_comic_info: RawConfigParser, comic_info: RawConfigParser) -> RawConfigParser:
    merged_info = deepcopy(comic_info)
    if merged_info.has_section("Pages"):
        del merged_info["Pages"]
    if extra_comic_info.has_section("Links Bar") and merged_info.has_section("Links Bar"):
        del merged_info["Links Bar"]
    for section in extra_comic_info.sections():
        if not merged_info.has_section(section):
            merged_info.add_section(section)
        for option in extra_comic_info.options(section):
            merged_info.set(section, option, extra_comic_info.get(section, option))
    return merged_info
