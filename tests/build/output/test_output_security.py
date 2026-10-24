import os
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from jinja2 import Environment, DictLoader
from core import rendering_utils
from build.content.page_models import validate_tag_name


class TestOutputSecurity(TestCase):
    def test_tag_paths_reject_traversal_and_documented_invalid_characters(self):
        for tag in [".", "..", "../outside", "a/b", "a\\b", "C:drive", "bad\x00", "trailing."]:
            with self.subTest(tag=tag), self.assertRaisesRegex(ValueError, "info.toml"):
                validate_tag_name(tag, "your_content/comics/001/info.toml")
        for tag in ["Normal tag", "José", "A & B", "part-one"]:
            validate_tag_name(tag, "info.ini")

    def test_output_writer_rejects_escape_before_creating_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root / "outside/index.html"
            outside.parent.mkdir()
            outside.write_text("original")
            with (patch.dict(os.environ, OUTPUT_DIR=str(root / "build")),
                  patch.object(rendering_utils, "jinja_environment", Environment(loader=DictLoader({"tagged.tpl": "changed"}))),
                  patch.object(rendering_utils, "build_md_page", return_value=None)):
                for path in ["tagged/../../outside/index.html", str(outside), "C:\\outside\\index.html"]:
                    with self.subTest(path=path), self.assertRaisesRegex(ValueError, "inside the output"):
                        rendering_utils.write_to_template("tagged", path)
                self.assertEqual("original", outside.read_text())
                self.assertFalse((root / "build").exists())
                rendering_utils.write_to_template("tagged", "tagged/Normal tag/index.html")
                self.assertEqual("changed", (root / "build/tagged/Normal tag/index.html").read_text())

    def test_output_writer_rejects_symlink_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "build").mkdir()
            (root / "outside").mkdir()
            try:
                (root / "build/link").symlink_to(root / "outside", target_is_directory=True)
            except OSError:
                self.skipTest("Creating symlinks is unavailable")
            with (patch.dict(os.environ, OUTPUT_DIR=str(root / "build")),
                  patch.object(rendering_utils, "jinja_environment", Environment()),
                  self.assertRaisesRegex(ValueError, "inside the output")):
                rendering_utils.write_to_template("tagged", "link/index.html")
