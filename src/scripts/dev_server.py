"""
Creates dev_server.py to run build_site.main, start an HTTP server, and watch for changes in
.tpl, .txt, .html, .md, .ini, and .toml files to rerun build_site.main in the background.
"""

import os
import sys
import logging
import shutil
import subprocess
import threading
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial
from typing import Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from build import build_site
from build.content.loaders import load_main_comic_info
from build.output.cms import DECAP_CMS_SCRIPT_PATH
from build.output.site_output import delete_output_file_space
from core import stdlib_utils
from core.logging_config import configure_logging

utils = stdlib_utils

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

WATCH_EXTENSIONS = {'.css', '.js', '.tpl', '.txt', '.html', '.md', '.ini', '.toml'}

HTTP_ROOT: str | None = None
PROJECT_ROOT: str | None = None
PREVIEW_SUBDIRECTORY = ""
SKIP_REBUILD = False
DECAP_CMS_DIST = Path("packages") / "decap-cms" / "dist"
LOCAL_DECAP_CMS_URL = "decap-cms.js"
IS_WINDOWS = os.name == "nt"


def get_decap_server_command(is_windows: bool) -> tuple[str, str]:
    return "npx.cmd" if is_windows else "npx", "decap-server"


DECAP_SERVER_COMMAND = get_decap_server_command(IS_WINDOWS)


def parse_args(argv: list[str] | None = None):
    parser = build_site.create_argument_parser(description="Auto-rebuilding comic_git development server")
    parser.add_argument(
        "--decap-cms-repo",
        type=Path,
        help=(
            "Load the built Decap CMS bundle from a local Decap checkout. This also enables "
            "--cms-local-backend. Build the checkout's decap-cms package before starting the server."
        ),
    )
    return parser.parse_args(argv)


def resolve_decap_cms_dist(repo: Path) -> Path:
    repo = repo.expanduser().resolve()
    dist = repo / DECAP_CMS_DIST
    bundle = dist / "decap-cms.js"
    if not bundle.is_file():
        raise FileNotFoundError(
            f"Local Decap CMS bundle not found at {bundle}. "
            "Build the checkout's decap-cms package before starting the development server."
        )
    return dist


def install_local_decap_cms(http_root: str, dist: Path) -> None:
    admin_dir = Path(http_root) / "admin"
    index_path = admin_dir / "index.html"
    if not index_path.is_file():
        raise FileNotFoundError(
            f"Generated CMS entry point not found at {index_path}. "
            "Enable CMS output in the host comic before using --decap-cms-repo."
        )

    html = index_path.read_text(encoding="utf-8")
    if html.count(DECAP_CMS_SCRIPT_PATH) != 1:
        raise RuntimeError(
            "Generated CMS entry point did not contain exactly one expected engine-owned Decap CMS path: "
            f"{DECAP_CMS_SCRIPT_PATH}"
        )

    shutil.copytree(
        dist,
        admin_dir,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("*.map"),
    )
    index_path.write_text(html.replace(DECAP_CMS_SCRIPT_PATH, LOCAL_DECAP_CMS_URL), encoding="utf-8")
    logger.info("Loaded local Decap CMS bundle from %s", dist)


def build_site_and_install_decap(build_args: list[Any], decap_dist: Path | None) -> None:
    build_site.main(*build_args)
    if decap_dist is not None:
        if HTTP_ROOT is None:
            raise RuntimeError("HTTP root was not initialized before installing local Decap CMS.")
        install_local_decap_cms(HTTP_ROOT, decap_dist)


def start_decap_server() -> subprocess.Popen:
    if PROJECT_ROOT is None:
        raise RuntimeError("Project root was not initialized before starting the Decap local backend.")
    try:
        process = subprocess.Popen(DECAP_SERVER_COMMAND, cwd=PROJECT_ROOT)
    except OSError as e:
        raise RuntimeError(
            "Could not start the Decap local backend. Install Node.js and make sure 'npx decap-server' works."
        ) from e
    logger.info("Started Decap local backend (PID %s).", process.pid)
    return process


def stop_decap_server(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        logger.info("Decap local backend already stopped.")
        return

    logger.info("Stopping Decap local backend (PID %s).", process.pid)
    if IS_WINDOWS:
        # npx can launch a Node child beneath its command wrapper on Windows.
        # Stop the whole tree so the proxy cannot outlive this development server.
        subprocess.run(
            ("taskkill", "/PID", str(process.pid), "/T", "/F"),
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        process.terminate()

    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        logger.warning("Decap local backend did not stop within five seconds; killing it.")
        process.kill()
        process.wait()


class PreviewRequestHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        request_path = path.split("?", 1)[0].split("#", 1)[0]
        prefix = PREVIEW_SUBDIRECTORY.rstrip("/")
        if prefix and (request_path == prefix or request_path.startswith(prefix + "/")):
            path = request_path[len(prefix):] or "/"
        return super().translate_path(path)


class WatchdogEventHandler(FileSystemEventHandler):
    def __init__(self, observer: Observer, args: list[Any], decap_dist: Path | None = None):
        super().__init__()
        self.observer = observer
        self.build_args = args
        self.decap_dist = decap_dist

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
                    build_site_and_install_decap(self.build_args, self.decap_dist)
                except Exception:
                    logger.exception("Build failed after file change")
                # Drain remaining events
                if hasattr(self.observer, "event_queue"):
                    try:
                        self.observer.event_queue.queue.clear()
                    except Exception:
                        logger.exception("Failed to clear watchdog event queue")
                SKIP_REBUILD = False


def watch_and_rebuild(build_args: list[Any], decap_dist: Path | None = None) -> Observer:
    if PROJECT_ROOT is None:
        raise RuntimeError("Project root was not initialized before starting the file watcher.")
    observer = Observer()
    event_handler = WatchdogEventHandler(observer, build_args, decap_dist)
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

    stdlib_utils.find_project_root()
    PROJECT_ROOT = os.getcwd()

    # Get build args
    args = parse_args()
    if args.decap_cms_repo is not None:
        args.cms_local_backend = True
    build_site.apply_cli_environment_overrides(args)
    build_args = [
        args.delete_scheduled_posts,
        args.publish_all_comics,
        args.cms_local_backend,
    ]

    # Set HTTP_ROOT
    comic_info = load_main_comic_info()
    _comic_url, subdirectory = stdlib_utils.get_comic_url(comic_info)
    PREVIEW_SUBDIRECTORY = subdirectory
    output_dir = stdlib_utils.get_output_dir()
    if args.decap_cms_repo is not None and not output_dir:
        raise ValueError(
            "--decap-cms-repo requires a generated output directory so local bundle assets "
            "cannot be left in the host repository."
        )
    HTTP_ROOT = os.path.abspath(output_dir) if output_dir else PROJECT_ROOT
    decap_dist = (
        resolve_decap_cms_dist(args.decap_cms_repo)
        if args.decap_cms_repo is not None
        else None
    )
    decap_server = start_decap_server() if args.cms_local_backend else None
    observer = None
    clean_output = False

    try:
        # Initial build
        build_site_and_install_decap(build_args, decap_dist)
        logger.info("")

        # Start watcher thread
        observer = watch_and_rebuild(build_args, decap_dist)
        watcher_thread = threading.Thread(target=start_observer, args=[observer], daemon=True)
        watcher_thread.start()

        # Start HTTP server (blocking)
        try:
            start_http_server(subdirectory)
        except KeyboardInterrupt:
            pass
        clean_output = True
    finally:
        if observer is not None:
            observer.stop()
        if decap_server is not None:
            stop_decap_server(decap_server)
        if clean_output:
            logger.info("Web server stopped. Deleting auto-generated files...")
            os.chdir(PROJECT_ROOT)
            delete_output_file_space(comic_info)


if __name__ == "__main__":
    main()
