import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from build.site_builder import build_and_publish_comic_pages
from build.content.loaders import load_main_comic_info
from build.content.site_config import get_extra_comic_info, get_extra_comics_list
from build.output.site_output import copy_output_assets, copy_site_root_files, setup_output_file_space
from core import utils
from core.logging_config import configure_logging
from core.models import ComicBuildResult
from core.utils import checkpoint, print_processing_times
from integrations.hooks import run_hook
from integrations.rss import build_rss_feed_from_job, get_rss_feed_jobs

logger = logging.getLogger(__name__)


def add_inputs_to_env_vars(inputs: str):
    """
    Get a string from the named environment variable, break up the string into individual key/value pairs,
    and then add each key/value pair as a new environment variable.

    The strings must match the format `KEY:VALUE`, with each pair on a separate line.
    Leading and trailing spaces are stripped from both the KEY and VALUE.
    """
    for input_pair in utils.str_to_list(os.getenv(inputs, ""), "\n"):
        if not input_pair:
            continue
        try:
            k, v = utils.str_to_list(input_pair, ":", 1)
        except ValueError:
            logger.warning("Invalid key-value pair for input: %r", input_pair)
        else:
            os.environ[k] = v


def main(delete_scheduled_posts: bool = False, publish_all_comics: bool = False):
    configure_logging()
    checkpoint("Start", clear=True)

    # Pull values from the INPUTS and SECRETS env vars and turn them into individual env vars
    add_inputs_to_env_vars("INPUTS")
    add_inputs_to_env_vars("SECRETS")

    # Get site-wide settings for this comic
    utils.find_project_root()
    comic_info = load_main_comic_info()
    comic_url, utils.BASE_DIRECTORY = utils.get_comic_url(comic_info)
    theme = comic_info.get("Comic Settings", "Theme", fallback="default")

    checkpoint("Get comic settings")

    run_hook(theme, "preprocess", [comic_info])

    checkpoint("Preprocessing hook")

    # Set up the output file space
    setup_output_file_space(comic_info)
    checkpoint("Setup output file space")

    # Build any extra comics that may be needed
    comic_results = []
    extra_comic_values = {}
    for extra_comic in get_extra_comics_list(comic_info):
        logger.info("Building Extra Comic: %s", extra_comic)
        extra_comic_info = get_extra_comic_info(extra_comic, comic_info)
        extra_comic_output_dir = os.path.join(utils.get_output_dir(), extra_comic)
        if extra_comic_output_dir:
            os.makedirs(extra_comic_output_dir, exist_ok=True)
        comic_data_dicts, extra_global_values = build_and_publish_comic_pages(
            comic_url, extra_comic.strip("/") + "/", extra_comic_info, delete_scheduled_posts,
            publish_all_comics
        )
        comic_results.append(
            ComicBuildResult(
                comic_folder=extra_comic.strip("/") + "/",
                comic_info=extra_comic_info,
                comic_data_dicts=comic_data_dicts,
                global_values=extra_global_values,
            )
        )
        extra_comic_values[extra_comic] = comic_data_dicts[-1] if comic_data_dicts else {}

    # Build and publish pages for the main comic
    logger.info("Building main comic")
    comic_data_dicts, global_values = build_and_publish_comic_pages(
        comic_url, "", comic_info, delete_scheduled_posts, publish_all_comics, extra_comic_values
    )
    main_comic_result = ComicBuildResult(
        comic_folder="",
        comic_info=comic_info,
        comic_data_dicts=comic_data_dicts,
        global_values=global_values,
    )
    comic_results.append(main_comic_result)

    # Build the RSS feed
    for feed_job in get_rss_feed_jobs(comic_results):
        build_rss_feed_from_job(feed_job)
    checkpoint("Build RSS feed")

    output_dir = utils.get_output_dir()
    if output_dir:
        copy_output_assets(output_dir)
        checkpoint("Copy extra files to output directory")
    copy_site_root_files(output_dir)
    checkpoint("Copy site_root files")

    run_hook(theme, "postprocess", [comic_info, comic_data_dicts, global_values])

    checkpoint("Postprocessing hook")

    print_processing_times()


def parse_args(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description='Manual build of comic_git')
    parser.add_argument(
        "-d",
        "--delete-scheduled-posts",
        action="store_true",
        help="Deletes scheduled post content when the script is run. USE AT YOUR OWN RISK! You can discard your "
             "changes in GitHub Desktop if you accidentally delete important files."
    )
    parser.add_argument(
        "-p",
        "--publish-all-comics",
        action="store_true",
        help="Will publish all comics, even ones with a publish date set in the future."
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        help="Override the output directory for this build. Defaults to the OUTPUT_DIR environment variable, "
             "or 'build' if OUTPUT_DIR is unset."
    )
    return parser.parse_args(argv)


def apply_cli_environment_overrides(args: argparse.Namespace) -> None:
    if args.output_dir is not None:
        os.environ["OUTPUT_DIR"] = args.output_dir


if __name__ == "__main__":
    args = parse_args()
    apply_cli_environment_overrides(args)
    try:
        main(args.delete_scheduled_posts, args.publish_all_comics)
    except Exception as e:
        # If the repo is not running in GitHub, raise the error normally
        if not os.getenv("GITHUB_REPOSITORY"):
            raise
        # Otherwise, log the error so it's readable in GitHub Actions logs.
        logger.exception("Build failed")
        logger.error("============= ERROR =============\n%s\n=================================", e)
