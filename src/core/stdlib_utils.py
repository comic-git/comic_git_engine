import html
import json
import logging
import os
import re
from configparser import RawConfigParser
from copy import deepcopy
from urllib.parse import urljoin

from build.content.content_paths import get_comic_social_media_paths
from time import strftime, perf_counter_ns

logger = logging.getLogger(__name__)

BASE_DIRECTORY = ""
PROCESSING_TIMES: list[tuple[str, float]] = []

social_media_data_by_comic: dict[str, dict] = {}


def web_path(rel_path: str) -> str:
    if rel_path.startswith("/"):
        return BASE_DIRECTORY + rel_path
    return rel_path


def get_output_dir() -> str:
    return os.getenv("OUTPUT_DIR", "build")


def get_comic_url(comic_info: RawConfigParser) -> tuple[str, str]:
    # Let user-defined comic domain and base directory override all other values
    comic_domain = comic_info.get("Comic Settings", "Comic domain", fallback=None)
    base_directory = comic_info.get("Comic Settings", "Comic subdirectory", fallback=None)
    if comic_domain is None:
        # If we have a CNAME file, use that for the comic domain
        if os.path.isfile("CNAME"):
            with open("CNAME") as f:
                comic_domain = f.read().strip('/')
                base_directory = ""
        # If this is running in GitHub and the domain and base directory were not user-defined, derive them here
        elif "GITHUB_REPOSITORY" in os.environ:
            repo_author, repo_name = os.environ["GITHUB_REPOSITORY"].split("/")
            if not comic_domain:
                comic_domain = f"{repo_author}.github.io"
            if base_directory is None:
                base_directory = repo_name
                if base_directory.lower() == f"{repo_author.lower()}.github.io":
                    # In this case, GitHub will try to deploy to http://<username>.github.io/ so we unset base_directory
                    base_directory = ""
    # Helpful error for dumb schmucks trying to build locally for the first time
    if not comic_domain:
        raise ValueError(
            'Set "Comic domain" in the [Comic Settings] section of your comic_info.ini file '
            'before building your site locally. Please see the comic_git documentation for more information.'
        )
    if comic_domain.startswith("http://"):
        comic_domain = comic_domain.replace("http://", "https://")
    if not comic_domain.startswith("http"):
        comic_domain = "https://" + comic_domain
    # Clean up values and make sure we don't have extraneous slashes
    comic_domain = comic_domain.strip("/")
    base_directory = base_directory.strip("/")
    if base_directory:
        base_directory = "/" + base_directory
    comic_url = comic_domain + base_directory
    logger.info("Base URL: %s, base subdirectory: %s", comic_url, base_directory)
    return comic_url, base_directory


def str_to_list(s: str, delimiter: str = ",", max_split: int = -1) -> list[str]:
    """
    split(), but with extra stripping of white space and leading/trailing delimiters
    """
    if not s:
        return []
    return [item.strip(" ") for item in s.strip(delimiter + " ").split(delimiter, max_split)]


def find_project_root():
    while not os.path.exists("your_content"):
        last_cwd = os.getcwd()
        os.chdir("..")
        if os.getcwd() == last_cwd:
            raise FileNotFoundError("Couldn't find a folder in the path matching 'your_content'. Make sure you're "
                                    "running this script from within the comic_git repository.")


def read_info(filepath, to_dict=False):
    try:
        with open(filepath, "rb") as f:
            info_string = f.read().decode("utf-8")
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Configuration file not found: {filepath}\n"
            f"Verify the file path is correct and the file exists."
        ) from e
    try:
        if not re.search(r"^\[.*?]", info_string):
            info_string = "[DEFAULT]\n" + info_string
        info = RawConfigParser()
        info.optionxform = str
        info.read_string(info_string)
        if to_dict:
            # TODO: Support multiple sections
            if not list(info.keys()) == ["DEFAULT"]:
                raise NotImplementedError("Configs with multiple sections not yet supported")
            return dict(info["DEFAULT"])
        return info
    except Exception as e:
        raise ValueError(
            f"Error parsing configuration file {filepath}: {e}\n"
            f"Verify the file is the correct format with each uncommented line matching the format <option> = <value>"
        ) from e


def pick_data(social_media_data: dict, template_name: str) -> dict:
    # If the template name isn't defined, use `base` instead
    if template_name not in social_media_data:
        return social_media_data.get("base", {})
    # Pull data for the given template and check if it has an `_inherits` field.
    data = deepcopy(social_media_data[template_name])
    inherits = data.get("_inherits")
    if inherits:
        # If there is an `_inherits` field defined, load data from that and apply current data on top of it.
        d = pick_data(social_media_data, inherits)
        d.update(data)
        data = d
        del data["_inherits"]
    return data


def get_social_media_data(
        comic_info: RawConfigParser, comic_data_dict: dict, template_name: str, html_path: str,
        custom_json_path: str = None,
        custom_social_media_data: dict | None = None,
) -> dict:
    """
    :param comic_info: Config data for comic_info.ini file.
    :param comic_data_dict: All comic data for the site.
    :param template_name: Template name for the page being built.
    :param html_path: The HTML path for the page being built.
    :param custom_json_path: If a special social_media.json file has been defined, pass the path in here
        and this function will use it.
    :return:
    """
    global social_media_data_by_comic
    if custom_social_media_data is not None:
        social_media_data = {"comic": custom_social_media_data}
    elif custom_json_path and os.path.isfile(custom_json_path):
        try:
            with open(custom_json_path) as f:
                social_media_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON in social_media.json file: {custom_json_path}\n"
                f"Verify the file contains valid JSON syntax."
            ) from e
        except IOError as e:
            raise ValueError(
                f"Error reading social_media.json file: {custom_json_path}\n"
                f"Verify the file exists and is readable."
            ) from e
    else:
        # Get the social media data for the given comic_folder (lets extra comics have different data)
        social_media_data = social_media_data_by_comic.get(comic_data_dict["comic_folder"])
    # Load social media data from the file if it's not loaded yet, or create default data
    if not social_media_data:
        for filepath in get_comic_social_media_paths(comic_data_dict["comic_folder"]):
            if os.path.isfile(filepath):
                with open(filepath) as f:
                    social_media_data = json.load(f)
                break
        else:
            social_media_data = {
                "base": {
                    "og:type": "website",
                    "og:site_name": "_comic_name",
                    "og:title": "_title",
                    "og:description": "_comic_description",
                    "og:url": "_url",
                    "og:image": "_preview_image",
                },
                "comic": {
                    "og:type": "article",
                    "og:site_name": "_comic_name",
                    "og:title": "_title",
                    "og:description": "_post_text",
                    "og:url": "_url",
                    "og:image": "_thumbnail",
                    "og:image:alt": "_alt_text",
                },
                "latest": {
                    "_inherits": "comic",
                },
            }
        social_media_data_by_comic[comic_data_dict["comic_folder"]] = social_media_data
    # Parse social media data and apply dynamic data as needed
    data = pick_data(social_media_data, template_name)
    # Iterate through all the values in the data dict, applying dynamic data where appropriate
    comic_url = comic_data_dict["comic_url"]
    if not comic_url.endswith("/"):
        comic_url += "/"
    if html_path.endswith("index.html"):
        html_path = html_path[:-10]
    html_path = urljoin(comic_url, html_path)
    comic_page = comic_data_dict.get("page")
    preview_image = "your_content/images/preview_image.png"
    page_thumbnail = comic_page.thumbnail_path if comic_page is not None else None
    page_screen_reader_text = (
        comic_page.images[0].screen_reader_text
        if comic_page is not None and comic_page.images
        else ""
    )
    for k, v in data.items():
        if v == "_comic_name":
            data[k] = comic_info.get("Comic Info", "Comic name")
        elif v == "_comic_description":
            data[k] = comic_info.get("Comic Info", "Description")
        elif v == "_url":
            data[k] = html_path
        elif v == "_title":
            data[k] = comic_data_dict["_title"]
        elif v == "_preview_image":
            data[k] = urljoin(comic_url, preview_image)
        elif v == "_thumbnail":
            data[k] = urljoin(comic_url, page_thumbnail or preview_image)
        elif v == "_post_text":
            data[k] = html.escape(comic_data_dict["post_md"])
        elif v == "_alt_text":
            data[k] = page_screen_reader_text
    return data


def checkpoint(s: str, clear: bool = False) -> None:
    global PROCESSING_TIMES
    if clear:
        PROCESSING_TIMES = [(s, perf_counter_ns())]
    else:
        PROCESSING_TIMES.append((s, perf_counter_ns()))


def print_processing_times() -> None:
    last_processed_time = None
    logger.info("")
    for name, t in PROCESSING_TIMES:
        if last_processed_time is not None:
            logger.info("%s: %.2f ms", name, (t - last_processed_time) / 1_000_000)
        last_processed_time = t
    logger.info("Total time: %.2f ms", (PROCESSING_TIMES[-1][1] - PROCESSING_TIMES[0][1]) / 1_000_000)
