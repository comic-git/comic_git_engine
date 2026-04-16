import os
import sys
import traceback
from collections import defaultdict
from configparser import RawConfigParser
from typing import Dict, List

import core.utils as utils
from build.site_config import get_pages_list
from integrations.hooks import run_hook


def write_html_files(comic_folder: str, comic_info: RawConfigParser, comic_data_dicts: List[Dict], global_values: Dict):
    template_folders = ["comic_git_engine/templates"]
    theme = comic_info.get("Comic Settings", "Theme", fallback="default")
    if theme:
        template_folders.insert(0, f"your_content/themes/{theme}/templates")
        if comic_folder:
            template_folders.insert(0, f"your_content/themes/{theme}/templates/{comic_folder}")
    print(f"Template folders: {template_folders}")
    utils.build_jinja_environment(comic_info, template_folders)
    utils.build_markdown_parser(comic_info)
    print("Writing {} comic pages...".format(len(comic_data_dicts)))
    for comic_data_dict in comic_data_dicts:
        html_path = f"{comic_folder}comic/{comic_data_dict['page_name']}/index.html"
        custom_social_media_path = os.path.join(comic_data_dict["page_dir"], "social_media.json")
        comic_data_dict.update(global_values)
        comic_data_dict["social_media"] = utils.get_social_media_data(
            comic_info, comic_data_dict, "comic", html_path, custom_social_media_path
        )
        utils.write_to_template("comic", html_path, comic_data_dict)
    write_other_pages(comic_folder, comic_info, comic_data_dicts, global_values)
    run_hook(global_values["theme"], "build_other_pages", [comic_folder, comic_info, comic_data_dicts])


def write_other_pages(comic_folder: str, comic_info: RawConfigParser, comic_data_dicts: List[Dict],
                      global_values: Dict):
    base_data_dict = {}
    if not comic_data_dicts:
        print("You're publishing a website with no comic pages. Are you sure you want that??", file=sys.stderr)
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
            print(f"Failed to create '{filename}' from 'tagged' template", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
