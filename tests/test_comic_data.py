import os
import tempfile
from collections import OrderedDict
from configparser import RawConfigParser
from unittest import TestCase
from unittest.mock import patch

from build import comic_data


class TestComicData(TestCase):

    def make_comic_info(self):
        comic_info = RawConfigParser()
        comic_info.add_section("Comic Settings")
        comic_info.set("Comic Settings", "Date format", "%B %d, %Y")
        comic_info.set("Comic Settings", "On comic click", "Next comic")
        comic_info.set("Comic Settings", "Theme", "default")
        comic_info.add_section("Archive")
        comic_info.set("Archive", "Date format", "%Y-%m-%d")
        comic_info.add_section("Transcripts")
        comic_info.set("Transcripts", "Enable transcripts", "True")
        return comic_info

    def test_format_user_variable_preserves_page_name_and_normalizes_other_keys(self):
        self.assertEqual("_post_date", comic_data.format_user_variable("Post date"))
        self.assertEqual("_this_page_is_full_of_spiders_1", comic_data.format_user_variable("This page is full of spiders!!1"))
        self.assertEqual("page_name", comic_data.format_user_variable("page_name"))

    def test_get_ids_handles_first_middle_and_last_pages(self):
        pages = [{"page_name": "001"}, {"page_name": "002"}, {"page_name": "003"}]

        self.assertEqual(
            {
                "first_id": "001",
                "previous_id": "001",
                "current_id": "001",
                "next_id": "002",
                "last_id": "003",
            },
            comic_data.get_ids(pages, 0),
        )
        self.assertEqual(
            {
                "first_id": "001",
                "previous_id": "001",
                "current_id": "002",
                "next_id": "003",
                "last_id": "003",
            },
            comic_data.get_ids(pages, 1),
        )
        self.assertEqual(
            {
                "first_id": "001",
                "previous_id": "002",
                "current_id": "003",
                "next_id": "003",
                "last_id": "003",
            },
            comic_data.get_ids(pages, 2),
        )

    @patch("build.comic_data.run_hook", return_value=None)
    @patch("build.comic_data.get_transcripts", return_value=OrderedDict({"English": "<p>Transcript</p>\n"}))
    def test_create_comic_data_builds_expected_fields(self, mock_get_transcripts, _mock_run_hook):
        comic_info = self.make_comic_info()
        page_info = {
            "page_name": "001",
            "Post date": "January 02, 2024",
            "Title": "Chapter One",
            "Alt text": '<tagged>',
            "image_file_names": ["page_1.png", "page_2.png"],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = os.getcwd()
            page_dir = os.path.join(temp_dir, "your_content", "comics", "001")
            os.makedirs(page_dir)
            files = {
                os.path.join(temp_dir, "your_content", "before post text.txt"): "before",
                os.path.join(temp_dir, "your_content", "before post text.html"): "<b>html before</b>",
                os.path.join(page_dir, "post.txt"): "main body",
                os.path.join(temp_dir, "your_content", "after post text.txt"): "after",
                os.path.join(temp_dir, "your_content", "after post text.html"): "<i>html after</i>",
            }
            for path, text in files.items():
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
            try:
                os.chdir(temp_dir)
                data = comic_data.create_comic_data("", comic_info, page_info, "001", "001", "001", "002", "002")
            finally:
                os.chdir(cwd)

        self.assertEqual("Chapter One", data["page_title"])
        self.assertEqual("Chapter One", data["_title"])
        self.assertEqual("next comic", data["_on_comic_click"])
        self.assertEqual("2024-01-02", data["archive_post_date"])
        self.assertEqual("before\n\n<b>html before</b>\n\nmain body\n\nafter\n\n<i>html after</i>", data["post_md"])
        self.assertIn("<p>before</p>", data["post_html"])
        self.assertEqual("&lt;tagged&gt;", data["escaped_alt_text"])
        self.assertEqual(OrderedDict({"English": "<p>Transcript</p>\n"}), data["transcripts"])
        self.assertEqual(
            ["your_content/comics/001/page_1.png", "your_content/comics/001/page_2.png"],
            data["comic_paths"],
        )
        mock_get_transcripts.assert_called_once_with("", comic_info, "001")

    @patch("build.comic_data.run_hook", return_value=None)
    @patch("build.comic_data.get_transcripts", return_value=OrderedDict())
    def test_create_comic_data_uses_filename_and_existing_title_overrides(self, _mock_get_transcripts, _mock_run_hook):
        comic_info = self.make_comic_info()
        page_info = {
            "page_name": "002",
            "Post date": "January 03, 2024",
            "image_file_names": ["cover-image.png"],
            "_title": "Explicit Internal Title",
            "_on_comic_click": "FIRST COMIC",
        }

        data = comic_data.create_comic_data("", comic_info, page_info, "001", "001", "002", "003", "003")

        self.assertEqual("cover-image", data["page_title"])
        self.assertEqual("Explicit Internal Title", data["_title"])
        self.assertEqual("first comic", data["_on_comic_click"])

    @patch("build.comic_data.run_hook", side_effect=lambda *_args: {"hooked": True, **_args[2][-1]})
    @patch("build.comic_data.get_transcripts", return_value=OrderedDict())
    def test_create_comic_data_applies_hook_result(self, _mock_get_transcripts, _mock_run_hook):
        comic_info = self.make_comic_info()
        page_info = {
            "page_name": "003",
            "Post date": "January 04, 2024",
            "image_file_names": [],
        }

        data = comic_data.create_comic_data("", comic_info, page_info, "001", "002", "003", "003", "003")

        self.assertTrue(data["hooked"])
        self.assertEqual("", data["page_title"])

    @patch("build.comic_data.create_comic_data")
    def test_build_comic_data_dicts_preserves_order_and_navigation_ids(self, mock_create_comic_data):
        comic_info = self.make_comic_info()
        page_info_list = [
            {"page_name": "001", "Post date": "January 01, 2024"},
            {"page_name": "002", "Post date": "January 02, 2024"},
        ]
        mock_create_comic_data.side_effect = lambda comic_folder, comic_info, page_info, **ids: {
            "page_name": page_info["page_name"],
            **ids,
        }

        data = comic_data.build_comic_data_dicts("", comic_info, page_info_list)

        self.assertEqual(["001", "002"], [item["page_name"] for item in data])
        self.assertEqual("001", data[0]["current_id"])
        self.assertEqual("002", data[1]["current_id"])
