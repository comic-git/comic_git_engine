import os
from configparser import RawConfigParser
from unittest import TestCase
from unittest.mock import call, patch

from build.output import rendering


MUT = "build.output.rendering."


class TestRendering(TestCase):

    def make_comic_info(self):
        comic_info = RawConfigParser()
        comic_info.add_section("Comic Settings")
        comic_info.set("Comic Settings", "Theme", "theme-name")
        return comic_info

    @patch(MUT + "utils.write_to_template")
    @patch(MUT + "utils.get_social_media_data", side_effect=lambda *_args: {"path": _args[3]})
    @patch(MUT + "get_pages_list", return_value=[
        {"template_name": "index", "title": ""},
        {"template_name": "404", "title": ""},
        {"template_name": "latest", "title": "Latest Page"},
        {"template_name": "about", "title": "About"},
        {"template_name": "tagged", "title": ""},
    ])
    @patch(MUT + "write_tagged_pages")
    def test_write_other_pages_handles_root_pages_extra_comics_and_title_overrides(
            self,
            mock_write_tagged_pages,
            _mock_get_pages_list,
            mock_social_media,
            mock_write_to_template,
    ):
        comic_info = self.make_comic_info()
        comic_data_dicts = [{"_title": "Comic Title", "page_name": "001"}]
        global_values = {"comic_url": "https://example.com"}

        rendering.write_other_pages("extras/story", comic_info, comic_data_dicts, global_values)

        mock_write_tagged_pages.assert_called_once()
        self.assertEqual(
            [
                call("index", os.path.join("extras/story", "index.html"), {"_title": "Comic Title", "page_name": "001", "comic_url": "https://example.com", "social_media": {"path": os.path.join("extras/story", "index.html")}}),
                call("404", os.path.join("extras/story", "404.html"), {"_title": "Comic Title", "page_name": "001", "comic_url": "https://example.com", "social_media": {"path": os.path.join("extras/story", "404.html")}}),
                call("latest", os.path.join("extras/story", "latest", "index.html"), {"_title": "Latest Page", "page_name": "001", "comic_url": "https://example.com", "social_media": {"path": os.path.join("extras/story", "latest", "index.html")}}),
                call("about", os.path.join("extras/story", "about", "index.html"), {"_title": "About", "page_name": "001", "comic_url": "https://example.com", "social_media": {"path": os.path.join("extras/story", "about", "index.html")}}),
            ],
            mock_write_to_template.call_args_list,
        )
        self.assertEqual(4, mock_social_media.call_count)

    @patch(MUT + "utils.write_to_template")
    @patch(MUT + "utils.get_social_media_data", return_value={"x": 1})
    @patch(MUT + "get_pages_list", return_value=[
        {"template_name": "latest", "title": ""},
        {"template_name": "index", "title": ""},
    ])
    def test_write_other_pages_uses_empty_comic_defaults_and_skips_latest_when_no_pages(
            self,
            _mock_get_pages_list,
            _mock_social_media,
            mock_write_to_template,
    ):
        comic_info = self.make_comic_info()

        rendering.write_other_pages("", comic_info, [], {"comic_url": "https://example.com"})

        self.assertEqual(1, mock_write_to_template.call_count)
        args = mock_write_to_template.call_args_list[0].args
        self.assertEqual("index", args[0])
        self.assertEqual("index.html", args[1])
        self.assertEqual("Index", args[2]["_title"])

    @patch(MUT + "utils.write_to_template", side_effect=[None, RuntimeError("boom"), None])
    @patch(MUT + "utils.get_social_media_data", return_value={"x": 1})
    def test_write_tagged_pages_groups_characters_and_tags_and_handles_write_failures(
            self,
            _mock_social_media,
            mock_write_to_template,
    ):
        comic_info = self.make_comic_info()
        pages = [
            {"page_name": "001", "_characters": ["Alice"], "_tags": ["mystery"]},
            {"page_name": "002", "_characters": ["Alice", "Bob"], "_tags": ["mystery", "action"]},
        ]

        rendering.write_tagged_pages(comic_info, pages, {"comic_url": "https://example.com"})

        filenames = [call.args[1] for call in mock_write_to_template.call_args_list]
        self.assertEqual(
            [
                "tagged/Alice/index.html",
                "tagged/mystery/index.html",
                "tagged/Bob/index.html",
                "tagged/action/index.html",
            ],
            filenames,
        )

    @patch(MUT + "run_hook")
    @patch(MUT + "write_other_pages")
    @patch(MUT + "utils.write_to_template")
    @patch(MUT + "utils.get_social_media_data", return_value={"card": "ok"})
    @patch(MUT + "utils.build_markdown_parser")
    @patch(MUT + "utils.build_jinja_environment")
    def test_write_html_files_uses_theme_template_precedence_and_custom_social_media_path(
            self,
            mock_build_jinja_environment,
            _mock_build_markdown_parser,
            _mock_social_media,
            mock_write_to_template,
            mock_write_other_pages,
            mock_run_hook,
    ):
        comic_info = self.make_comic_info()
        comic_data_dicts = [{"page_name": "001", "page_dir": "your_content/extras/story/comics/001"}]
        global_values = {"theme": "theme-name", "comic_url": "https://example.com"}

        rendering.write_html_files("extras/story/", comic_info, comic_data_dicts, global_values)

        mock_build_jinja_environment.assert_called_once_with(
            comic_info,
            [
                "your_content/themes/theme-name/templates/extras/story/",
                "your_content/themes/theme-name/templates",
                "comic_git_engine/templates",
            ],
        )
        mock_write_to_template.assert_called_once()
        self.assertEqual("comic", mock_write_to_template.call_args.args[0])
        self.assertEqual("extras/story/comic/001/index.html", mock_write_to_template.call_args.args[1])
        mock_write_other_pages.assert_called_once_with("extras/story/", comic_info, comic_data_dicts, global_values)
        mock_run_hook.assert_called_once_with("theme-name", "build_other_pages", ["extras/story/", comic_info, comic_data_dicts])
