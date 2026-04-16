import os
import shutil
from configparser import RawConfigParser

from build.site_config import get_extra_comics_list, get_pages_list
from core.utils import read_info


def delete_output_file_space(comic_info: RawConfigParser = None):
    output_dir = os.getenv("OUTPUT_DIR", "")
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
    shutil.copy("favicon.ico", output_dir)
