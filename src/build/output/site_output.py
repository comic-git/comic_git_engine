import os
import shutil
from configparser import RawConfigParser

from build.content.site_config import get_extra_comics_list, get_pages_list
from core.utils import get_output_dir, read_info

SITE_ROOT_SOURCE = os.path.join("your_content", "site_root")


def delete_output_file_space(comic_info: RawConfigParser = None):
    output_dir = get_output_dir()
    if output_dir:
        shutil.rmtree(output_dir, ignore_errors=True)
        return
    shutil.rmtree("comic", ignore_errors=True)
    if os.path.isfile("feed.xml"):
        os.remove("feed.xml")
    if comic_info is None:
        comic_info = read_info("your_content/comic_info.ini")
    for page in get_pages_list(comic_info):
        if page["template_name"] == "index":
            if os.path.exists("index.html"):
                os.remove("index.html")
        elif page["template_name"] == "404":
            if os.path.exists("404.html"):
                os.remove("404.html")
        else:
            if os.path.exists(page["template_name"]):
                shutil.rmtree(page["template_name"])
    for comic in get_extra_comics_list(comic_info):
        if os.path.exists(comic):
            shutil.rmtree(comic)


def setup_output_file_space(comic_info: RawConfigParser):
    delete_output_file_space(comic_info)


def copy_output_assets(output_dir: str):
    if not output_dir:
        return
    shutil.copytree("comic_git_engine/css", os.path.join(output_dir, "comic_git_engine/css"))
    shutil.copytree("comic_git_engine/js", os.path.join(output_dir, "comic_git_engine/js"))
    shutil.copytree("your_content", os.path.join(output_dir, "your_content"))


def copy_site_root_files(output_dir: str) -> None:
    if not os.path.isdir(SITE_ROOT_SOURCE):
        raise NotADirectoryError(
            "Missing required folder: your_content/site_root\n"
            "Create that folder in your host repo so comic_git can copy root-level site files into the built output."
        )

    output_root = output_dir or "."
    for current_root, _dir_names, file_names in os.walk(SITE_ROOT_SOURCE):
        rel_dir = os.path.relpath(current_root, SITE_ROOT_SOURCE)
        target_dir = output_root if rel_dir == "." else os.path.join(output_root, rel_dir)
        os.makedirs(target_dir, exist_ok=True)
        for file_name in file_names:
            source_path = os.path.join(current_root, file_name)
            target_path = os.path.join(target_dir, file_name)
            if os.path.exists(target_path):
                print(f"WARNING: Overwriting existing output file with site_root file: {target_path}")
            shutil.copy2(source_path, target_path)
