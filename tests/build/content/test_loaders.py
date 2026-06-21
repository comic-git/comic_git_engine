from configparser import RawConfigParser
from unittest import TestCase
from unittest.mock import patch

from build.content import loaders


MUT = "build.content.loaders."


class TestLoadMainComicInfo(TestCase):
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


class TestLoadExtraComicInfo(TestCase):
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
