import html
import os
import re
from configparser import RawConfigParser
from time import strptime, strftime
from typing import Dict, List

from markdown2 import Markdown

from build.content.transcripts import get_transcripts
from integrations.hooks import run_hook


MARKDOWN = Markdown(extras=["strike", "break-on-newline", "markdown-in-html"])


def format_user_variable(k: str) -> str:
    k = re.sub(r"[^a-z0-9_]+", "_", k.lower()).strip("_")
    if k not in ["page_name"]:
        k = "_" + k
    return k


def get_ids(comic_list: List[Dict], index):
    return {
        "first_id": comic_list[0]["page_name"],
        "previous_id": comic_list[max(0, index - 1)]["page_name"],
        "current_id": comic_list[index]["page_name"],
        "next_id": comic_list[min(len(comic_list) - 1, index + 1)]["page_name"],
        "last_id": comic_list[-1]["page_name"]
    }


def create_comic_data(comic_folder: str, comic_info: RawConfigParser, page_info: dict,
                      first_id: str, previous_id: str, current_id: str, next_id: str, last_id: str):
    t = strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{t}] Building page {page_info['page_name']}...")
    page_dir = f"your_content/{comic_folder}comics/{page_info['page_name']}/"
    archive_date_format = comic_info.get("Archive", "Date format")
    if archive_date_format:
        archive_post_date = strftime(
            archive_date_format,
            strptime(
                page_info["Post date"],
                comic_info.get("Comic Settings", "Date format")
            )
        )
    else:
        archive_post_date = page_info["Post date"]
    post_md = []
    post_text_paths = [
        f"your_content/{comic_folder}before post text.txt",
        f"your_content/{comic_folder}before post text.html",
        page_dir + "post.txt",
        f"your_content/{comic_folder}after post text.txt",
        f"your_content/{comic_folder}after post text.html",
    ]
    for post_text_path in post_text_paths:
        if os.path.isfile(post_text_path):
            with open(post_text_path, "rb") as f:
                post_md.append(f.read().decode("utf-8"))
    post_md = "\n\n".join(post_md)
    post_html = MARKDOWN.convert(post_md)
    if "Title" in page_info:
        page_title = page_info["Title"]
    elif page_info["image_file_names"]:
        page_title = os.path.splitext(page_info["image_file_names"][0])[0]
    else:
        page_title = ""
    d = {
        "page_title": page_title,
        "page_dir": page_dir,
        "comic_paths": [os.path.join(page_dir, f) for f in page_info["image_file_names"]],
        "thumbnail_path": os.path.join(page_dir, "_thumbnail.jpg"),
        "escaped_alt_text": html.escape(page_info.get("Alt text", "")),
        "first_id": first_id,
        "previous_id": previous_id,
        "current_id": current_id,
        "next_id": next_id,
        "last_id": last_id,
        "archive_post_date": archive_post_date,
        "post_md": post_md,
        "post_html": post_html,
        "transcripts": get_transcripts(comic_folder, comic_info, page_info["page_name"]),
    }
    d.update({format_user_variable(k): v for k, v in page_info.items()})
    if "_title" not in page_info:
        d["_title"] = page_title
    if "_on_comic_click" not in d:
        d["_on_comic_click"] = comic_info.get("Comic Settings", "On comic click", fallback="Next comic")
    d["_on_comic_click"] = d["_on_comic_click"].lower()
    theme = comic_info.get("Comic Settings", "Theme", fallback="default")
    hook_result = run_hook(theme, "extra_comic_dict_processing", [comic_folder, comic_info, d])
    if hook_result:
        d = hook_result
    return d


def build_comic_data_dicts(comic_folder: str, comic_info: RawConfigParser, page_info_list: List[Dict]) -> List[Dict]:
    return [
        create_comic_data(comic_folder, comic_info, page_info, **get_ids(page_info_list, i))
        for i, page_info in enumerate(page_info_list)
    ]
