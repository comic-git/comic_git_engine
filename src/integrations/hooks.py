import logging
import os
import sys
from importlib import import_module
from typing import Any, List

logger = logging.getLogger(__name__)


def run_hook(theme: str, func: str, args: List[Any]) -> Any:
    if os.path.exists(f"your_content/themes/{theme}/scripts/hooks.py"):
        current_path = os.path.abspath(".")
        if current_path not in sys.path:
            sys.path.append(current_path)
            logger.debug("Path updated: %s", sys.path)
        hooks = import_module(f"your_content.themes.{theme}.scripts.hooks")
        if hasattr(hooks, func):
            method = getattr(hooks, func)
            return method(*args)
    return None
