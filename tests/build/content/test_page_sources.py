import json
import os
import tempfile
from collections import OrderedDict
from configparser import RawConfigParser
from datetime import datetime
from unittest import TestCase

from build.content import page_sources


class TestPageSources(TestCase):
    def make_comic_info(self, date_format="%B %d, %Y"):
        comic_info = RawConfigParser()
        comic_info.add_section("Comic Settings")
        comic_info.set("Comic Settings", "Date format", date_format)
        comic_info.add_section("Transcripts")
        comic_info.set("Transcripts", "Enable transcripts", "True")
        return comic_info

    def round_trip_migrated_date(self, legacy_date: str, date_format: str) -> tuple[str, str]:
        comic_info = self.make_comic_info(date_format)
        source = page_sources.PageSource(
            post_date=page_sources.legacy_date_to_iso(legacy_date, date_format),
            images=["page.png"],
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "info.toml")
            with open(path, "w", encoding="utf-8") as f:
                f.write(page_sources.serialize_page_source_to_toml(source))

            loaded = page_sources.load_page_source_from_toml(path)

        page_info = page_sources.page_source_to_legacy_page_info(loaded, comic_info)
        return page_info["Post date"], loaded.post_date

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

    def test_migrated_display_date_formats_remain_equivalent(self):
        cases = [
            ("August 01, 2000", "%B %d, %Y"),
            ("Aug 01, 2000", "%b %d, %Y"),
        ]
        for legacy_date, date_format in cases:
            with self.subTest(date_format=date_format):
                round_tripped_date, iso_date = self.round_trip_migrated_date(legacy_date, date_format)

            self.assertEqual("2000-08-01", iso_date)
            self.assertEqual(
                datetime.strptime(legacy_date, date_format).date(),
                datetime.strptime(round_tripped_date, date_format).date(),
            )

    def test_migrated_fixed_width_date_formats_round_trip_exactly(self):
        cases = [
            ("2000-08-01", "%Y-%m-%d"),
            ("2000/08/01", "%Y/%m/%d"),
            ("08/01/2000", "%m/%d/%Y"),
            ("01/08/2000", "%d/%m/%Y"),
            ("20000801", "%Y%m%d"),
        ]
        for legacy_date, date_format in cases:
            with self.subTest(date_format=date_format):
                round_tripped_date, iso_date = self.round_trip_migrated_date(legacy_date, date_format)

            self.assertEqual("2000-08-01", iso_date)
            self.assertEqual(legacy_date, round_tripped_date)
