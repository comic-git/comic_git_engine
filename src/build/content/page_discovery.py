import json
import os
import re
import shutil
from datetime import datetime
from glob import iglob
from time import strptime
from typing import Dict, List, Tuple

from configparser import RawConfigParser
from pytz import timezone

from build.content import content_paths
from build.content.loaders import load_page_info
from build.content.transcripts import get_transcripts
from core import utils
from integrations.hooks import run_hook


def get_page_info_list(comic_folder: str, comic_info: RawConfigParser, delete_scheduled_posts: bool,
                       publish_all_comics: bool) -> Tuple[List[Dict], int]:
    date_format = comic_info.get("Comic Settings", "Date format")
    try:
        tz_info = timezone(comic_info.get("Comic Settings", "Timezone"))
    except Exception as e:
        raise ValueError(
            f"Invalid timezone specified in [Comic Settings] Timezone: {e}\n"
            f"Use a valid IANA timezone name (e.g., 'America/Los_Angeles', 'Europe/London', 'UTC'). "
            f"See https://en.wikipedia.org/wiki/List_of_tz_database_time_zones for a complete list."
        ) from e
    local_time = datetime.now(tz=tz_info)
    print(f"Local time is {local_time}")
    page_info_list = []
    scheduled_post_count = 0
    theme = comic_info.get("Comic Settings", "Theme", fallback="default")
    for page_path in iglob(f"your_content/{comic_folder}comics/*/"):
        page_path = page_path.replace("\\", "/")
        filepath, page_info = load_page_info(page_path)
        if page_info is None or filepath is None:
            _, legacy_path = content_paths.get_page_info_candidates(page_path)
            print(f"{page_path} is missing its {os.path.basename(legacy_path)} file. Skipping")
            continue
        try:
            post_date = tz_info.localize(datetime.strptime(page_info["Post date"], date_format))
        except ValueError as e:
            raise ValueError(
                f"Invalid 'Post date' in {filepath}: {page_info['Post date']}\n"
                f"The date format is '{date_format}'. Ensure the date matches this format exactly (case-sensitive)."
            ) from e
        if post_date > local_time and not publish_all_comics:
            scheduled_post_count += 1
            if delete_scheduled_posts:
                print(f"Deleting {page_path}")
                shutil.rmtree(page_path)
        else:
            filenames = page_info.get("Filenames") or page_info.get("Filename", "")
            if filenames:
                page_info["image_file_names"] = utils.str_to_list(filenames)
                for filename in page_info["image_file_names"]:
                    path = os.path.join(page_path, filename)
                    if not os.path.isfile(path):
                        raise FileNotFoundError(
                            f"Could not find comic image {path}\n"
                            f"Did you mistype the filename in the info.ini file? Remember that filenames and extensions "
                            f"are case-sensitive when building on GitHub."
                        )
            else:
                image_files = []
                for filename in os.listdir(page_path):
                    if filename.startswith("_"):
                        continue
                    if re.search(r"\.(jpg|jpeg|png|tif|tiff|gif|bmp|webp|webv|svg|eps)$", filename):
                        image_files.append(filename)
                page_info["image_file_names"] = sorted(image_files)
            page_info["page_name"] = os.path.basename(os.path.normpath(page_path))
            page_info["Storyline"] = page_info.get("Storyline", "")
            page_info["Characters"] = utils.str_to_list(page_info.get("Characters", ""))
            page_info["Tags"] = utils.str_to_list(page_info.get("Tags", ""))
            for key in page_info.copy():
                if key.startswith("!"):
                    del page_info[key]
            transcripts = get_transcripts(comic_folder, comic_info, page_info["page_name"])
            page_info["transcript_languages"] = list(transcripts.keys())
            hook_result = run_hook(theme, "extra_page_info_processing",
                                   [comic_folder, comic_info, page_path, page_info])
            if hook_result:
                page_info = hook_result
            print(page_info)
            page_info_list.append(page_info)

    page_info_list = sorted(
        page_info_list,
        key=lambda x: (strptime(x["Post date"], date_format), x["page_name"])
    )
    return page_info_list, scheduled_post_count


def save_page_info_json_file(comic_folder: str, page_info_list: List, scheduled_post_count: int):
    d = {
        "page_info_list": page_info_list,
        "scheduled_post_count": scheduled_post_count
    }
    output_dir = utils.get_output_dir()
    os.makedirs(os.path.join(output_dir, f"{comic_folder}comic"), exist_ok=True)
    with open(os.path.join(output_dir, f"{comic_folder}comic/page_info_list.json"), "w") as f:
        f.write(json.dumps(d))
