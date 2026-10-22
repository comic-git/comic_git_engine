import importlib.util
import tempfile
import threading
from functools import partial
from http.server import HTTPServer
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import urlopen

from build import build_site
from build.output.site_output import validate_hidden_path_policy

SCRIPT = Path(__file__).resolve().parents[2] / "src/scripts/dev_server.py"


class TestPreviewSecurity(TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("preview_security", SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_default_bind_and_explicit_lan(self):
        self.assertEqual("127.0.0.1", build_site.parse_args([], preview=True).listen)
        self.assertEqual("0.0.0.0", build_site.parse_args(["--listen", "0.0.0.0"], preview=True).listen)
        self.module.HTTP_ROOT = "."
        with patch.object(self.module, "HTTPServer") as server:
            self.module.start_http_server("")
            self.assertEqual(("127.0.0.1", 8000), server.call_args.args[0])
        with self.assertRaises(ValueError):
            validate_hidden_path_policy("", "")

    def test_http_denies_dotfiles_and_directory_listings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.html").write_text("public")
            (root / ".git").mkdir()
            (root / ".git/config").write_text("private")
            (root / "assets").mkdir()
            self.module.PREVIEW_SUBDIRECTORY = "/comic"
            server = HTTPServer(("127.0.0.1", 0), partial(self.module.PreviewRequestHandler, directory=tmp))
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                url = f"http://127.0.0.1:{server.server_port}"
                with urlopen(url + "/comic/") as response:
                    self.assertEqual(b"public", response.read())
                for path in ["/.git/config", "/%2egit/config", "/comic/.git/config", "/assets/"]:
                    with self.subTest(path=path), self.assertRaises(HTTPError) as caught:
                        urlopen(url + path)
                    self.assertEqual(404, caught.exception.code)
            finally:
                server.shutdown()
                server.server_close()
                worker.join()

    def test_symlink_and_index_symlink_cannot_escape_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "public"
            root.mkdir()
            secret = Path(tmp) / "secret.txt"
            secret.write_text("private")
            try:
                (root / "linked.txt").symlink_to(secret)
                (root / "index.html").symlink_to(secret)
            except OSError:
                self.skipTest("Creating symlinks is unavailable")
            handler = object.__new__(self.module.PreviewRequestHandler)
            handler.directory = str(root)
            for path in ["/linked.txt", "/"]:
                handler.path = path
                with patch.object(handler, "send_error") as error:
                    self.assertIsNone(handler.send_head())
                    error.assert_called_once_with(404)
