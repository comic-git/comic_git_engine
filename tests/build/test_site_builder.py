from configparser import RawConfigParser
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import DEFAULT, mock_open, patch

from build import site_builder


class TestLoadHomePageText(TestCase):
    def test_prefers_text_source_and_renders_markdown(self):
        reader = mock_open(read_data=b"# Welcome")

        with (
            patch.object(site_builder.os.path, "isfile", side_effect=lambda path: path.endswith(".txt")),
            patch("builtins.open", reader),
        ):
            result = site_builder.load_home_page_text("extras/story/")

        self.assertEqual("<h1>Welcome</h1>\n", result)
        reader.assert_called_once_with("your_content/extras/story/home page.txt", "rb")

    def test_warns_and_returns_empty_when_home_page_is_missing(self):
        with (
            patch.object(site_builder.os.path, "isfile", return_value=False),
            self.assertLogs("build.site_builder", level="WARNING") as logs,
        ):
            result = site_builder.load_home_page_text("")

        self.assertEqual("", result)
        self.assertIn("your_content/home page.*", logs.output[0])


class TestBuildAndPublishComicPages(TestCase):
    def make_config(self):
        comic_info = RawConfigParser()
        comic_info.add_section("Comic Info")
        comic_info.set("Comic Info", "Comic name", "Test Comic")
        comic_info.set("Comic Info", "Author", "Test Author")
        comic_info.set("Comic Info", "Description", "Test Description")
        comic_info.add_section("Comic Settings")
        comic_info.set("Comic Settings", "Theme", "default")
        comic_info.add_section("Archive")
        comic_info.set("Archive", "Use thumbnails", "True")
        return comic_info

    def test_builds_per_comic_pipeline_and_projection_context(self):
        comic_info = self.make_config()
        discovered_pages = [SimpleNamespace(page_name="001")]
        built_pages = [SimpleNamespace(page_name="001")]
        storylines = object()
        chapters = object()
        mocks_to_create = {
            name: DEFAULT
            for name in (
                "discover_pages",
                "build_comic_pages",
                "process_comic_images",
                "save_page_metadata",
                "load_home_page_text",
                "get_links_list",
                "get_storylines",
                "get_infinite_scroll_chapters",
                "load_webring_data",
                "run_hook",
                "write_html_files",
            )
        }

        with (
            patch.multiple(site_builder, **mocks_to_create) as mocks,
            patch.object(site_builder.utils, "BASE_DIRECTORY", "/base"),
            patch.object(site_builder.utils, "web_path", side_effect=lambda value: value),
            patch.object(site_builder.utils, "checkpoint"),
        ):
            mocks["discover_pages"].return_value = (discovered_pages, 2)
            mocks["build_comic_pages"].return_value = built_pages
            mocks["load_home_page_text"].return_value = "Home"
            mocks["get_links_list"].return_value = ["link"]
            mocks["get_storylines"].return_value = storylines
            mocks["get_infinite_scroll_chapters"].return_value = chapters
            mocks["load_webring_data"].return_value = {"webring": "data"}
            mocks["run_hook"].return_value = {"hooked": "value"}

            result_pages, global_values = site_builder.build_and_publish_comic_pages(
                "https://example.com/extras/story",
                "extras/story/",
                comic_info,
                False,
                True,
                {"bonus": {"page_name": "001"}},
            )

        self.assertIs(built_pages, result_pages)
        mocks["discover_pages"].assert_called_once_with("extras/story/", comic_info, False, True)
        mocks["build_comic_pages"].assert_called_once_with(
            "extras/story/", comic_info, discovered_pages
        )
        mocks["process_comic_images"].assert_called_once_with(comic_info, built_pages)
        mocks["save_page_metadata"].assert_called_once_with(
            "extras/story/", comic_info, built_pages, 2, site_builder.VERSION
        )
        mocks["get_storylines"].assert_called_once_with(comic_info, built_pages)
        mocks["get_infinite_scroll_chapters"].assert_called_once_with(comic_info, built_pages)
        self.assertIs(storylines, global_values["storylines"])
        self.assertIs(chapters, global_values["infinite_scroll_chapters"])
        self.assertEqual("/base/extras/story", global_values["comic_base_dir"])
        self.assertEqual("/base/your_content/extras/story", global_values["content_base_dir"])
        self.assertEqual("value", global_values["hooked"])
        self.assertEqual("data", global_values["webring"])
        mocks["write_html_files"].assert_called_once_with(
            "extras/story/", comic_info, built_pages, global_values
        )
