import json
import os
import tempfile
from configparser import RawConfigParser
from unittest import TestCase
from unittest.mock import patch

from build.content import page_discovery


MUT = "build.content.page_discovery."


class TestPageDiscovery(TestCase):

    def make_comic_info(self):
        comic_info = RawConfigParser()
        comic_info.add_section("Comic Settings")
        comic_info.set("Comic Settings", "Date format", "%B %d, %Y")
        comic_info.set("Comic Settings", "Timezone", "UTC")
        comic_info.set("Comic Settings", "Theme", "default")
        comic_info.add_section("Transcripts")
        comic_info.set("Transcripts", "Enable transcripts", "True")
        return comic_info

    def write_page(self, root, name, info_lines, extra_files=None):
        page_dir = os.path.join(root, "your_content", "comics", name)
        os.makedirs(page_dir, exist_ok=True)
        with open(os.path.join(page_dir, "info.ini"), "w", encoding="utf-8") as f:
            for line in info_lines:
                f.write(f"{line}\n")
        for file_name, content in (extra_files or {}).items():
            with open(os.path.join(page_dir, file_name), "w", encoding="utf-8") as f:
                f.write(content)
        return page_dir

    def test_get_page_info_list_rejects_invalid_timezone(self):
        comic_info = self.make_comic_info()
        comic_info.set("Comic Settings", "Timezone", "Not/AZone")

        with self.assertRaisesRegex(ValueError, "Invalid timezone specified"):
            page_discovery.get_page_info_list("", comic_info, False, False)

    @patch(MUT + "run_hook", return_value=None)
    @patch(MUT + "get_transcripts", side_effect=lambda *_args: {"English": "<p>x</p>\n"})
    def test_get_page_info_list_filters_and_normalizes_metadata(self, _mock_get_transcripts, _mock_run_hook):
        comic_info = self.make_comic_info()
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = os.getcwd()
            self.write_page(
                temp_dir,
                "b-page",
                [
                    "Post date = January 02, 2020",
                    "Characters = Alice, Bob",
                    "Tags = mystery, noir",
                    "!Draft note = hidden",
                    "Storyline = Arc 1",
                ],
                {
                    "page.png": "x",
                    "_hidden.png": "x",
                },
            )
            self.write_page(
                temp_dir,
                "a-page",
                [
                    "Post date = January 02, 2020",
                ],
                {
                    "a.png": "x",
                },
            )
            self.write_page(
                temp_dir,
                "future-page",
                [
                    "Post date = January 01, 2999",
                ],
                {
                    "future.png": "x",
                },
            )
            os.makedirs(os.path.join(temp_dir, "your_content", "comics", "missing-info"), exist_ok=True)
            try:
                os.chdir(temp_dir)
                page_info_list, scheduled_count = page_discovery.get_page_info_list("", comic_info, False, False)
            finally:
                os.chdir(cwd)

        self.assertEqual(1, scheduled_count)
        self.assertEqual(["a-page", "b-page"], [page["page_name"] for page in page_info_list])
        self.assertEqual(["a.png"], page_info_list[0]["image_file_names"])
        self.assertEqual(["page.png"], page_info_list[1]["image_file_names"])
        self.assertEqual(["Alice", "Bob"], page_info_list[1]["Characters"])
        self.assertEqual(["mystery", "noir"], page_info_list[1]["Tags"])
        self.assertNotIn("!Draft note", page_info_list[1])
        self.assertEqual(["English"], page_info_list[1]["transcript_languages"])

    @patch(MUT + "run_hook", side_effect=lambda theme, func, args: {**args[-1], "hooked": True})
    @patch(MUT + "get_transcripts", return_value={})
    def test_get_page_info_list_deletes_future_posts_and_respects_explicit_filenames(self, _mock_get_transcripts, _mock_run_hook):
        comic_info = self.make_comic_info()
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = os.getcwd()
            future_dir = self.write_page(
                temp_dir,
                "future-page",
                [
                    "Post date = January 01, 2999",
                ],
                {
                    "future.png": "x",
                },
            )
            self.write_page(
                temp_dir,
                "named-page",
                [
                    "Post date = January 01, 2020",
                    "Filenames = one.png, two.png",
                ],
                {
                    "one.png": "x",
                    "two.png": "x",
                },
            )
            try:
                os.chdir(temp_dir)
                page_info_list, scheduled_count = page_discovery.get_page_info_list("", comic_info, True, False)
            finally:
                os.chdir(cwd)

        self.assertEqual(1, scheduled_count)
        self.assertFalse(os.path.exists(future_dir))
        self.assertEqual(["one.png", "two.png"], page_info_list[0]["image_file_names"])
        self.assertTrue(page_info_list[0]["hooked"])

    def test_get_page_info_list_reads_info_toml(self):
        comic_info = self.make_comic_info()
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = os.getcwd()
            page_dir = os.path.join(temp_dir, "your_content", "comics", "001")
            os.makedirs(page_dir, exist_ok=True)
            with open(os.path.join(page_dir, "info.toml"), "w", encoding="utf-8") as f:
                f.write('post_date = "2020-01-02"\n')
                f.write('images = ["page.png"]\n')
                f.write('post_text = """\nBody text\n"""\n')
                f.write('\n[transcripts]\n')
                f.write('English = """\nTranscript text\n"""\n')
            with open(os.path.join(page_dir, "page.png"), "w", encoding="utf-8") as f:
                f.write("x")
            try:
                os.chdir(temp_dir)
                page_info_list, scheduled_count = page_discovery.get_page_info_list("", comic_info, False, False)
            finally:
                os.chdir(cwd)

        self.assertEqual(0, scheduled_count)
        self.assertEqual(["001"], [page["page_name"] for page in page_info_list])
        self.assertEqual(["page.png"], page_info_list[0]["image_file_names"])
        self.assertEqual(["English"], page_info_list[0]["transcript_languages"])
        self.assertTrue(page_info_list[0]["_toml_managed"])

    def test_save_page_info_json_file_uses_output_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"OUTPUT_DIR": temp_dir}, clear=False):
                page_discovery.save_page_info_json_file(
                    "extras/story/",
                    [{"page_name": "001"}],
                    2,
                )
            output_path = os.path.join(temp_dir, "extras", "story", "comic", "page_info_list.json")
            with open(output_path, "r", encoding="utf-8") as f:
                data = json.load(f)

        self.assertEqual(2, data["scheduled_post_count"])
        self.assertEqual("001", data["page_info_list"][0]["page_name"])

    def test_save_page_info_json_file_defaults_to_build_output_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                page_discovery.save_page_info_json_file(
                    "",
                    [{"page_name": "001"}],
                    1,
                )
                output_path = os.path.join(temp_dir, "build", "comic", "page_info_list.json")
                with open(output_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            finally:
                os.chdir(cwd)

        self.assertEqual(1, data["scheduled_post_count"])
        self.assertEqual("001", data["page_info_list"][0]["page_name"])
