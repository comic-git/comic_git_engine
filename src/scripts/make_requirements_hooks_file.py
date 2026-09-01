import logging
import os
import sys
from typing import Set

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from build.content.loaders import load_main_comic_info
from build.content.site_config import get_extra_comics_list, get_extra_comic_info
from core import utils
from core.logging_config import configure_logging

logger = logging.getLogger(__name__)


def get_requirements(theme: str) -> Set[str]:
    requirements_path = f"your_content/themes/{theme}/scripts/requirements.txt"
    if os.path.exists(requirements_path):
        with open(requirements_path) as f:
            return set(utils.str_to_list(f.read().replace("\r", ""), delimiter="\n"))
    return set()


def main():
    configure_logging()
    utils.find_project_root()
    comic_info = load_main_comic_info()
    theme = comic_info.get("Comic Settings", "Theme", fallback="default")
    requirements = get_requirements(theme)
    logger.debug("Hook requirements for main comic: %s", requirements)
    # Build any extra comics that may be needed
    for extra_comic in get_extra_comics_list(comic_info):
        logger.info("Checking hook requirements for Extra Comic: %s", extra_comic)
        extra_comic_info = get_extra_comic_info(extra_comic, comic_info)
        theme = extra_comic_info.get("Comic Settings", "Theme", fallback="default")
        if theme:
            requirements.update(get_requirements(theme))
            logger.debug("Hook requirements after %s: %s", extra_comic, requirements)
    with open("comic_git_engine/requirements_hooks.txt", "w") as f:
        f.write("\n".join(requirements))


if __name__ == "__main__":
    main()
