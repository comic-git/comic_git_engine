"""
Creates dev_server.py to run build_site.main, start an HTTP server, and watch for changes in
.tpl, .txt, .html, .md, and .ini files to rerun build_site.main in the background.
"""

import os
import sys
import threading
import traceback
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Any

import build_site
import utils

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("""
ERROR: The 'watchdog' library is required for detecting file changes.
Install it by running:
    pip install watchdog
Then re-run this script.""", file=sys.stderr)
    exit(1)

WATCH_EXTENSIONS = {'.tpl', '.txt', '.html', '.md', '.ini'}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTTP_ROOT = None
SRC_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '../..'))
SKIP_REBUILD = False


class WatchdogEventHandler(FileSystemEventHandler):
    def __init__(self, observer: Observer, args: list[Any]):
        super().__init__()
        self.observer = observer
        self.build_args = args

    def on_any_event(self, event):
        global SKIP_REBUILD
        if SKIP_REBUILD:
            print("Skipping watch due to rebuilding")
            return
        # print(event)
        # Only rebuild if the file extension matches
        if not event.is_directory:
            ext = os.path.splitext(event.src_path)[1].lower()
            if ext in WATCH_EXTENSIONS:
                print(f"Change detected: {event.src_path}. Rebuilding...")
                SKIP_REBUILD = True
                os.chdir(SRC_ROOT)
                try:
                    build_site.main(*self.build_args)
                except Exception:
                    traceback.print_exc(file=sys.stderr)
                # Drain remaining events
                if hasattr(self.observer, "event_queue"):
                    try:
                        self.observer.event_queue.queue.clear()
                    except Exception:
                        traceback.print_exc(file=sys.stderr)
                SKIP_REBUILD = False


def watch_and_rebuild(build_args: list[Any]) -> Observer:
    observer = Observer()
    event_handler = WatchdogEventHandler(observer, build_args)
    observer.schedule(event_handler, SRC_ROOT, recursive=True)
    return observer


def start_observer(observer: Observer):
    observer.start()
    print("Started watchdog observer.")
    try:
        observer.join()
    except KeyboardInterrupt:
        pass


def start_http_server(subdirectory: str):
    os.chdir(HTTP_ROOT)
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    url = f"http://localhost:{server_address[1]}{subdirectory}"
    print(f"Starting web server.\nGo to {url} in your browser to view your site.\nUse Ctrl+C to stop the server.\n")
    httpd.serve_forever()


def main():
    global HTTP_ROOT

    # Change working directory
    os.chdir(SRC_ROOT)

    # Get build args
    args = build_site.parse_args()
    build_args = [args.delete_scheduled_posts, args.publish_all_comics]

    # Set HTTP_ROOT
    comic_info = build_site.read_info("your_content/comic_info.ini")
    comic_url, subdirectory = utils.get_comic_url(comic_info)
    if not subdirectory:
        # If subdirectory is empty, leave HTTP_ROOT the same as SRC_ROOT
        HTTP_ROOT = SRC_ROOT
    else:
        # Otherwise, put HTTP_ROOT one directory up so the website is served properly.
        HTTP_ROOT = os.path.abspath(os.path.join(SRC_ROOT, ".."))

    # Initial build
    build_site.main(*build_args)
    print("")

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
    print("\nWeb server stopped. Deleting auto-generated files...")
    os.chdir(SRC_ROOT)
    build_site.delete_output_file_space()


if __name__ == "__main__":
    main()
