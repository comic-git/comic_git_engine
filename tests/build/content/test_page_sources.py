import json
import os
import tempfile
from collections import OrderedDict
from configparser import RawConfigParser
from unittest import TestCase

from build.content import page_sources


class TestPageSources(TestCase):
    def make_comic_info(self):
        comic_info = RawConfigParser()
        comic_info.add_section("Comic Settings")
        comic_info.set("Comic Settings", "Date format", "%B %d, %Y")
        comic_info.add_section("Transcripts")
        comic_info.set("Transcripts", "Enable transcripts", "True")
        return comic_info

    def test_load_legacy_page_source_collects_page_folder_content(self):
        comic_info = self.make_comic_info()
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = os.getcwd()
            page_dir = os.path.join(temp_dir, "your_content", "comics", "001")
            os.makedirs(page_dir, exist_ok=True)
            with open(os.path.join(page_dir, "info.ini"), "w", encoding="utf-8") as f:
                f.write("Post date = January 02, 2024\n")
                f.write("Title = Chapter One\n")
                f.write("Alt text = Alt words\n")
                f.write("Storyline = Arc 1\n")
                f.write("Characters = Alice, Bob\n")
                f.write("Tags = noir, mystery\n")
                f.write("Mood = tense\n")
            with open(os.path.join(page_dir, "page.png"), "w", encoding="utf-8") as f:
                f.write("x")
            with open(os.path.join(page_dir, "post.txt"), "w", encoding="utf-8") as f:
                f.write("Page body")
            with open(os.path.join(page_dir, "English.md"), "w", encoding="utf-8") as f:
                f.write("**Transcript**")
            with open(os.path.join(page_dir, "social_media.json"), "w", encoding="utf-8") as f:
                json.dump({"comic": {"og:title": "Override"}}, f)
            try:
                os.chdir(temp_dir)
                source = page_sources.load_legacy_page_source(page_dir, "", comic_info)
            finally:
                os.chdir(cwd)

        self.assertEqual("2024-01-02", source.post_date)
        self.assertEqual(["page.png"], source.images)
        self.assertEqual("Chapter One", source.title)
        self.assertEqual("Page body", source.post_text)
        self.assertEqual(OrderedDict({"English": "**Transcript**"}), source.transcripts)
        self.assertEqual({"og:title": "Override"}, source.social_media)
        self.assertEqual(OrderedDict({"Mood": "tense"}), source.extra)

    def test_page_source_round_trips_through_toml(self):
        source = page_sources.PageSource(
            post_date="2024-01-02",
            title="Chapter One",
            images=["page_1.png", "page_2.png"],
            post_text="Body text",
            alt_text="Alt words",
            storyline="Arc 1",
            characters=["Alice", "Bob"],
            tags=["noir", "mystery"],
            transcripts=OrderedDict({"English": "Transcript"}),
            social_media={"og:title": "Override"},
            extra=OrderedDict({"Mood": "tense"}),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "info.toml")
            with open(path, "w", encoding="utf-8") as f:
                f.write(page_sources.serialize_page_source_to_toml(source))

            loaded = page_sources.load_page_source_from_toml(path)

        self.assertEqual(source, loaded)

    def test_page_source_toml_handles_escaped_multiline_text(self):
        source = page_sources.PageSource(
            post_date="2024-01-02",
            title='Chapter "One"',
            images=["page_1.png"],
            post_text='Line 1\n\nPath C:\\comics\\001\nTriple quotes: """\nBackslash n: \\n\nUnicode: café 漫画',
            alt_text='Alt text with """ and C:\\alt',
            transcripts=OrderedDict({
                "English": 'Transcript line\nLiteral slash: \\ and quotes: """\nEmoji: 🎨',
            }),
            social_media={"og:title": 'Title with "quotes" and C:\\path'},
            extra=OrderedDict({"Mood": 'tense """ C:\\mood ñ'}),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "info.toml")
            with open(path, "w", encoding="utf-8") as f:
                f.write(page_sources.serialize_page_source_to_toml(source))

            loaded = page_sources.load_page_source_from_toml(path)

        self.assertEqual(source, loaded)
