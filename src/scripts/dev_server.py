"""
Creates dev_server.py to run build_site.main, start an HTTP server, and watch for changes in
.tpl, .txt, .html, .md, .ini, and .toml files to rerun build_site.main in the background.
"""

import os
import sys
import logging
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial
from typing import Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from build import build_site
from build.content.loaders import load_main_comic_info
from build.output.site_output import delete_output_file_space
from core import utils
from core.logging_config import configure_logging

logger = logging.getLogger(__name__)
configure_logging()

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    logger.error("""
ERROR: The 'watchdog' library is required for detecting file changes.
Install it by running:
    pip install watchdog
Then re-run this script.""")
    exit(1)

WATCH_EXTENSIONS = {'.tpl', '.txt', '.html', '.md', '.ini', '.toml'}

HTTP_ROOT: str | None = None
PROJECT_ROOT: str | None = None
PREVIEW_SUBDIRECTORY = ""
SKIP_REBUILD = False


class PreviewRequestHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        request_path = path.split("?", 1)[0].split("#", 1)[0]
        prefix = PREVIEW_SUBDIRECTORY.rstrip("/")
        if prefix and (request_path == prefix or request_path.startswith(prefix + "/")):
            path = request_path[len(prefix):] or "/"
        return super().translate_path(path)


class WatchdogEventHandler(FileSystemEventHandler):
    def __init__(self, observer: Observer, args: list[Any]):
        super().__init__()
        self.observer = observer
        self.build_args = args

    def on_any_event(self, event):
        global SKIP_REBUILD
        if SKIP_REBUILD:
            logger.debug("Skipping watch due to rebuilding")
            return
        # Only rebuild if the file extension matches
        if not event.is_directory:
            ext = os.path.splitext(event.src_path)[1].lower()
            if ext in WATCH_EXTENSIONS:
                logger.info("Change detected: %s. Rebuilding...", event.src_path)
                SKIP_REBUILD = True
                os.chdir(PROJECT_ROOT)
                try:
                    build_site.main(*self.build_args)
                except Exception:
                    logger.exception("Build failed after file change")
                # Drain remaining events
                if hasattr(self.observer, "event_queue"):
                    try:
                        self.observer.event_queue.queue.clear()
                    except Exception:
                        logger.exception("Failed to clear watchdog event queue")
                SKIP_REBUILD = False


def watch_and_rebuild(build_args: list[Any]) -> Observer:
    if PROJECT_ROOT is None:
        raise RuntimeError("Project root was not initialized before starting the file watcher.")
    observer = Observer()
    event_handler = WatchdogEventHandler(observer, build_args)
    observer.schedule(event_handler, PROJECT_ROOT, recursive=True)
    return observer


def start_observer(observer: Observer):
    observer.start()
    logger.info("Started watchdog observer.")
    try:
        observer.join()
    except KeyboardInterrupt:
        pass


def start_http_server(subdirectory: str):
    if HTTP_ROOT is None:
        raise RuntimeError("HTTP root was not initialized before starting the preview server.")
    server_address = ('', 8000)
    request_handler = partial(PreviewRequestHandler, directory=HTTP_ROOT)
    httpd = HTTPServer(server_address, request_handler)
    url = f"http://localhost:{server_address[1]}{subdirectory}"
    logger.info("Starting web server.\nGo to %s in your browser to view your site.\nUse Ctrl+C to stop the server.", url)
    httpd.serve_forever()


def main():
    global HTTP_ROOT, PREVIEW_SUBDIRECTORY, PROJECT_ROOT

    utils.find_project_root()
    PROJECT_ROOT = os.getcwd()

    # Get build args
    args = build_site.parse_args()
    build_site.apply_cli_environment_overrides(args)
    build_args = [args.delete_scheduled_posts, args.publish_all_comics]

    # Set HTTP_ROOT
    comic_info = load_main_comic_info()
    _comic_url, subdirectory = utils.get_comic_url(comic_info)
    PREVIEW_SUBDIRECTORY = subdirectory
    output_dir = utils.get_output_dir()
    HTTP_ROOT = os.path.abspath(output_dir) if output_dir else PROJECT_ROOT

    # Initial build
    build_site.main(*build_args)
    logger.info("")

    # Start watcher thread
    observer = watch_and_rebuild(build_args)
    watcher_thread = threading.Thread(target=start_observer, args=[observer], daemon=True)
    watcher_thread.start()

    # Start HTTP server (blocking)
    try:
        start_http_server(subdirectory)
    except KeyboardInterrupt:
        pass

    observer.stop()
    logger.info("Web server stopped. Deleting auto-generated files...")
    os.chdir(PROJECT_ROOT)
    delete_output_file_space(comic_info)


if __name__ == "__main__":
    main()
