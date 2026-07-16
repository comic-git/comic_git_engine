import logging
import os
from collections import defaultdict
from configparser import RawConfigParser
from typing import Dict, List

from build.content.content_paths import get_page_social_media_path
from core import utils
from build.content.site_config import get_pages_list
from integrations.hooks import run_hook

logger = logging.getLogger(__name__)


def write_html_files(comic_folder: str, comic_info: RawConfigParser, comic_data_dicts: List[Dict], global_values: Dict):
    template_folders = ["comic_git_engine/templates"]
    theme = comic_info.get("Comic Settings", "Theme", fallback="default")
    if theme:
        template_folders.insert(0, f"your_content/themes/{theme}/templates")
        if comic_folder:
            template_folders.insert(0, f"your_content/themes/{theme}/templates/{comic_folder}")
    logger.debug("Template folders: %s", template_folders)
    utils.build_jinja_environment(comic_info, template_folders)
    utils.build_markdown_parser(comic_info)
    logger.info("Writing %s comic pages", len(comic_data_dicts))
    for comic_data_dict in comic_data_dicts:
        html_path = f"{comic_folder}comic/{comic_data_dict['page_name']}/index.html"
        custom_social_media_path = None if comic_data_dict.get("_social_media") else get_page_social_media_path(comic_data_dict["page_dir"])
        comic_data_dict.update(global_values)
        comic_data_dict["social_media"] = utils.get_social_media_data(
            comic_info,
            comic_data_dict,
            "comic",
            html_path,
            custom_json_path=custom_social_media_path,
            custom_social_media_data=comic_data_dict.get("_social_media"),
        )
        utils.write_to_template("comic", html_path, comic_data_dict)
    write_other_pages(comic_folder, comic_info, comic_data_dicts, global_values)
    run_hook(global_values["theme"], "build_other_pages", [comic_folder, comic_info, comic_data_dicts])


def write_other_pages(comic_folder: str, comic_info: RawConfigParser, comic_data_dicts: List[Dict],
                      global_values: Dict):
    base_data_dict = {}
    if not comic_data_dicts:
        logger.warning("You're publishing a website with no comic pages. Are you sure you want that?")
        base_data_dict.update({"_title": "Index"})
    else:
        base_data_dict.update(comic_data_dicts[-1])
    base_data_dict.update(global_values)
    pages_list = get_pages_list(comic_info)
    for page in pages_list:
        if page["template_name"] == "tagged":
            write_tagged_pages(comic_info, comic_data_dicts, base_data_dict)
            continue
        if page["template_name"].lower() in ("index", "404"):
            html_path = f"{page['template_name']}.html"
        else:
            html_path = os.path.join(page['template_name'], "index.html")
        if comic_folder:
            html_path = os.path.join(comic_folder, html_path)
        if page["template_name"] == "latest" and not comic_data_dicts:
            continue
        data_dict = base_data_dict.copy()
        if page["title"]:
            data_dict["_title"] = page["title"]
        data_dict["social_media"] = utils.get_social_media_data(comic_info, data_dict, page["template_name"], html_path)
        utils.write_to_template(page["template_name"], html_path, data_dict)


def write_tagged_pages(comic_info: RawConfigParser, comic_data_dicts: List[Dict], global_values: Dict):
    if not comic_data_dicts:
        return
    tags = defaultdict(list)
    for page in comic_data_dicts:
        for character in page.get("_characters", []):
            tags[character].append(page)
        for tag in page.get("_tags", []):
            tags[tag].append(page)
    for tag, pages in tags.items():
        data_dict = global_values.copy()
        data_dict.update({
            "_title": f"Posts tagged with {tag}",
            "tag": tag,
            "tagged_pages": pages
        })
        filename = f"tagged/{tag}/index.html"
        data_dict["social_media"] = utils.get_social_media_data(comic_info, data_dict, "tagged", filename)
        try:
            utils.write_to_template("tagged", filename, data_dict)
        except Exception:
            logger.exception("Failed to create '%s' from 'tagged' template", filename)
