import os
import tempfile
from configparser import RawConfigParser
from unittest import TestCase
from unittest.mock import patch

from build.content import loaders


MUT = "build.content.loaders."


class TestLoadMainComicInfo(TestCase):
    def write_toml(self, text: str) -> str:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = os.path.join(temp_dir.name, "comic_info.toml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    @patch(MUT + "load_legacy_comic_info")
    @patch(MUT + "os.path.isfile", side_effect=lambda path: path.endswith("comic_info.toml"))
    @patch(MUT + "load_main_comic_info_toml")
    def test_toml_wins_when_available(self, toml_loader, _mock_isfile, legacy_loader):
        comic_info = RawConfigParser()
        toml_loader.return_value = comic_info

        actual = loaders.load_main_comic_info()

        self.assertIs(comic_info, actual)
        legacy_loader.assert_not_called()

    @patch(MUT + "load_legacy_comic_info")
    @patch(MUT + "os.path.isfile", return_value=False)
    @patch(MUT + "load_main_comic_info_toml")
    def test_legacy_used_when_toml_missing(self, toml_loader, _mock_isfile, legacy_loader):
        comic_info = RawConfigParser()
        legacy_loader.return_value = comic_info

        actual = loaders.load_main_comic_info()

        self.assertIs(comic_info, actual)
        toml_loader.assert_not_called()
        legacy_loader.assert_called_once()

    def test_load_main_comic_info_toml_reads_comic_config(self):
        path = self.write_toml(
            """
[comic]
name = "TOML Comic"

[site]
date_format = "%Y-%m-%d"
"""
        )

        comic_info = loaders.load_main_comic_info_toml(path)

        self.assertEqual("TOML Comic", comic_info.get("Comic Info", "Comic name"))
        self.assertEqual("%Y-%m-%d", comic_info.get("Comic Settings", "Date format"))


class TestLoadExtraComicInfo(TestCase):
    def make_parent_info(self):
        comic_info = RawConfigParser()
        comic_info.optionxform = str
        comic_info.add_section("Comic Info")
        comic_info.set("Comic Info", "Comic name", "Main Comic")
        comic_info.add_section("Comic Settings")
        comic_info.set("Comic Settings", "Date format", "%B %d, %Y")
        comic_info.add_section("Pages")
        comic_info.set("Pages", "about", "About")
        comic_info.add_section("Links Bar")
        comic_info.set("Links Bar", "Home", "/")
        return comic_info

    def write_toml(self, text: str) -> str:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = os.path.join(temp_dir.name, "comic_info.toml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    @patch(MUT + "load_legacy_extra_comic_info")
    @patch(MUT + "os.path.isfile", side_effect=lambda path: path.endswith("comic_info.toml"))
    @patch(MUT + "load_extra_comic_info_toml")
    def test_toml_wins_when_available(self, toml_loader, _mock_isfile, legacy_loader):
        parent_info = RawConfigParser()
        extra_info = RawConfigParser()
        toml_loader.return_value = extra_info

        actual = loaders.load_extra_comic_info("extras/story", parent_info)

        self.assertIs(extra_info, actual)
        legacy_loader.assert_not_called()

    @patch(MUT + "load_legacy_extra_comic_info")
    @patch(MUT + "os.path.isfile", return_value=False)
    @patch(MUT + "load_extra_comic_info_toml")
    def test_legacy_used_when_toml_missing(self, toml_loader, _mock_isfile, legacy_loader):
        parent_info = RawConfigParser()
        extra_info = RawConfigParser()
        legacy_loader.return_value = extra_info

        actual = loaders.load_extra_comic_info("extras/story", parent_info)

        self.assertIs(extra_info, actual)
        toml_loader.assert_not_called()
        legacy_loader.assert_called_once()

    def test_load_extra_comic_info_toml_merges_override_with_parent(self):
        path = self.write_toml(
            """
[comic]
name = "Extra Comic"

[[links]]
name = "Cast"
url = "/cast/"
"""
        )

        extra_info = loaders.load_extra_comic_info_toml("extras/story", self.make_parent_info(), path)

        self.assertEqual("Extra Comic", extra_info.get("Comic Info", "Comic name"))
        self.assertEqual("%B %d, %Y", extra_info.get("Comic Settings", "Date format"))
        self.assertFalse(extra_info.has_section("Pages"))
        self.assertEqual("/cast/", extra_info.get("Links Bar", "Cast"))
        self.assertFalse(extra_info.has_option("Links Bar", "Home"))

    def test_load_extra_comic_info_toml_inherits_links_when_override_has_none(self):
        path = self.write_toml(
            """
[comic]
name = "Extra Comic"
"""
        )

        extra_info = loaders.load_extra_comic_info_toml("extras/story", self.make_parent_info(), path)

        self.assertEqual("/", extra_info.get("Links Bar", "Home"))
        self.assertFalse(extra_info.has_section("Pages"))


class TestLoadPageInfo(TestCase):
    def make_comic_info(self):
        comic_info = RawConfigParser()
        comic_info.add_section("Comic Settings")
        comic_info.set("Comic Settings", "Date format", "%B %d, %Y")
        return comic_info

    @patch(MUT + "load_legacy_page_info")
    @patch(MUT + "os.path.isfile", side_effect=lambda path: path.endswith("info.toml"))
    @patch(MUT + "load_page_info_toml")
    def test_toml_wins_when_available(self, toml_loader, _mock_isfile, legacy_loader):
        page_info = {"Post date": "January 01, 2020"}
        toml_loader.return_value = page_info

        actual_path, actual_page_info = loaders.load_page_info("your_content/comics/001/", self.make_comic_info())

        self.assertTrue(actual_path.endswith("info.toml"))
        self.assertEqual(page_info, actual_page_info)
        legacy_loader.assert_not_called()

    @patch(MUT + "load_legacy_page_info")
    @patch(MUT + "os.path.isfile", side_effect=lambda path: path.endswith("info.ini"))
    @patch(MUT + "load_page_info_toml")
    def test_legacy_used_when_toml_missing(self, toml_loader, _mock_isfile, legacy_loader):
        page_info = {"Post date": "January 01, 2020"}
        legacy_loader.return_value = page_info

        actual_path, actual_page_info = loaders.load_page_info("your_content/comics/001/", self.make_comic_info())

        self.assertTrue(actual_path.endswith("info.ini"))
        self.assertEqual(page_info, actual_page_info)
        toml_loader.assert_not_called()
        legacy_loader.assert_called_once()

    @patch(MUT + "load_legacy_page_info")
    @patch(MUT + "os.path.isfile", return_value=False)
    @patch(MUT + "load_page_info_toml")
    def test_returns_none_when_no_supported_files_exist(self, toml_loader, _mock_isfile, legacy_loader):
        actual_path, actual_page_info = loaders.load_page_info("your_content/comics/001/", self.make_comic_info())

        self.assertIsNone(actual_path)
        self.assertIsNone(actual_page_info)
        toml_loader.assert_not_called()
        legacy_loader.assert_not_called()
