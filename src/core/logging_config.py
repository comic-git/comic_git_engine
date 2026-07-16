import logging
import os


LOG_LEVEL_ENV_VAR = "COMIC_GIT_LOG_LEVEL"
DEFAULT_LOG_LEVEL = "INFO"
HUMAN_READABLE_FORMAT = "%(message)s"


def configure_logging(force: bool = False) -> None:
    level_name = os.getenv(LOG_LEVEL_ENV_VAR, DEFAULT_LOG_LEVEL).strip().upper()
    level = get_log_level(level_name)
    invalid_level_name = None
    if level is None:
        invalid_level_name = level_name
        level = logging.INFO
    logging.basicConfig(level=level, format=HUMAN_READABLE_FORMAT, force=force)
    if invalid_level_name is not None:
        logging.getLogger(__name__).warning(
            "Invalid %s value %r; using %s",
            LOG_LEVEL_ENV_VAR,
            invalid_level_name,
            DEFAULT_LOG_LEVEL,
        )


def get_log_level(level_name: str) -> int | None:
    if level_name.isdigit():
        return int(level_name)
    level = logging.getLevelName(level_name)
    if isinstance(level, int):
        return level
    return None
