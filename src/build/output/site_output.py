import json
import logging
import os
import shutil
from configparser import RawConfigParser

from build.content.loaders import load_main_comic_info
from build.content.site_config import get_extra_comics_list, get_pages_list
from build.output.cms import GENERATED_FILE_MARKER
from core.stdlib_utils import get_output_dir

logger = logging.getLogger(__name__)

SITE_ROOT_SOURCE = os.path.join("your_content", "site_root")
CMS_OUTPUT_FILES = (
    os.path.join("admin", "index.html"),
    os.path.join("admin", "config.yml"),
    os.path.join("admin", "comic-git-widgets.js"),
)
CMS_RUNTIME_MANIFEST_FILENAME = "comic_git_engine_manifest.json"
CMS_RUNTIME_MARKER = "comic_git_engine_decap_runtime"


def delete_output_file_space(comic_info: RawConfigParser = None):
    output_dir = get_output_dir()
    if output_dir:
        shutil.rmtree(output_dir, ignore_errors=True)
        return
    shutil.rmtree("comic", ignore_errors=True)
    if os.path.isfile("feed.xml"):
        os.remove("feed.xml")
    if comic_info is None:
        comic_info = load_main_comic_info()
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
    remove_generated_cms_files()


def remove_generated_cms_files(output_root: str = ".") -> None:
    for relative_path in CMS_OUTPUT_FILES:
        path = os.path.join(output_root, relative_path)
        if _has_generated_cms_marker(path):
            os.remove(path)
    admin_dir = os.path.join(output_root, "admin")
    _remove_generated_cms_runtime_directories(admin_dir)
    try:
        os.rmdir(admin_dir)
    except OSError:
        pass


def _has_generated_cms_marker(path: str) -> bool:
    if not os.path.isfile(path):
        return False
    try:
        with open(path, encoding="utf-8") as f:
            return GENERATED_FILE_MARKER in f.read(4096)
    except (OSError, UnicodeError):
        return False


def _remove_generated_cms_runtime_directories(admin_dir: str) -> None:
    vendor_dir = os.path.join(admin_dir, "vendor")
    if not os.path.isdir(vendor_dir):
        return
    for entry in os.scandir(vendor_dir):
        if entry.is_dir(follow_symlinks=False) and _has_generated_cms_runtime_marker(entry.path):
            shutil.rmtree(entry.path)
    try:
        os.rmdir(vendor_dir)
    except OSError:
        pass


def _has_generated_cms_runtime_marker(directory: str) -> bool:
    manifest_path = os.path.join(directory, CMS_RUNTIME_MANIFEST_FILENAME)
    if not os.path.isfile(manifest_path):
        return False
    try:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    return isinstance(manifest, dict) and manifest.get("asset_kind") == CMS_RUNTIME_MARKER


def setup_output_file_space(comic_info: RawConfigParser):
    delete_output_file_space(comic_info)


def copy_output_assets(output_dir: str):
    if not output_dir:
        return
    shutil.copytree("comic_git_engine/css", os.path.join(output_dir, "comic_git_engine/css"))
    shutil.copytree("comic_git_engine/js", os.path.join(output_dir, "comic_git_engine/js"))
    shutil.copytree("comic_git_engine/schemas", os.path.join(output_dir, "comic_git_engine/schemas"))
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
                logger.warning("Overwriting existing output file with site_root file: %s", target_path)
            shutil.copy2(source_path, target_path)
