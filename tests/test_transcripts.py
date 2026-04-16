import os
import tempfile
from collections import OrderedDict
from configparser import RawConfigParser
from unittest import TestCase

from build import transcripts


class TestTranscripts(TestCase):

    def make_comic_info(self):
        comic_info = RawConfigParser()
        comic_info.add_section("Transcripts")
        comic_info.set("Transcripts", "Enable transcripts", "True")
        return comic_info

    def test_load_transcripts_from_folder_prefers_md_and_skips_post_txt(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            page_dir = os.path.join(temp_dir, "page-1")
            os.makedirs(page_dir)
            with open(os.path.join(page_dir, "English.txt"), "w", encoding="utf-8") as f:
                f.write("plain text")
            with open(os.path.join(page_dir, "English.md"), "w", encoding="utf-8") as f:
                f.write("**markdown**")
            with open(os.path.join(page_dir, "post.txt"), "w", encoding="utf-8") as f:
                f.write("skip me")

            loaded = transcripts.load_transcripts_from_folder(temp_dir, "page-1")

        self.assertEqual(["English"], list(loaded.keys()))
        self.assertEqual("<p><strong>markdown</strong></p>\n", loaded["English"])

    def test_load_transcripts_from_folder_falls_back_to_latin_1(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            page_dir = os.path.join(temp_dir, "page-1")
            os.makedirs(page_dir)
            with open(os.path.join(page_dir, "Espanol.txt"), "wb") as f:
                f.write("caf\xe9".encode("latin-1"))

            loaded = transcripts.load_transcripts_from_folder(temp_dir, "page-1")

        self.assertEqual("<p>caf\xe9</p>\n", loaded["Espanol"])

    def test_get_transcripts_returns_empty_when_disabled(self):
        comic_info = self.make_comic_info()
        comic_info.set("Transcripts", "Enable transcripts", "False")

        self.assertEqual(OrderedDict(), transcripts.get_transcripts("", comic_info, "page-1"))

    def test_get_transcripts_loads_from_comic_folder_and_configured_folder(self):
        comic_info = self.make_comic_info()
        comic_info.set("Transcripts", "Default language", "French")
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = os.getcwd()
            comic_dir = os.path.join(temp_dir, "your_content", "comics", "page-1")
            extra_dir = os.path.join(temp_dir, "transcripts", "page-1")
            os.makedirs(comic_dir)
            os.makedirs(extra_dir)
            with open(os.path.join(comic_dir, "English.txt"), "w", encoding="utf-8") as f:
                f.write("english")
            with open(os.path.join(extra_dir, "French.txt"), "w", encoding="utf-8") as f:
                f.write("french")
            comic_info.set("Transcripts", "Transcripts folder", os.path.join(temp_dir, "transcripts"))
            try:
                os.chdir(temp_dir)
                loaded = transcripts.get_transcripts("", comic_info, "page-1")
            finally:
                os.chdir(cwd)

        self.assertEqual(["French", "English"], list(loaded.keys()))
        self.assertEqual("<p>french</p>\n", loaded["French"])
        self.assertEqual("<p>english</p>\n", loaded["English"])
