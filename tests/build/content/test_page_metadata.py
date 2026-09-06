import json
import os
import tempfile
from configparser import RawConfigParser
from unittest import TestCase
from unittest.mock import patch

from build.content import page_metadata
from build.content.page_models import ComicImage, ComicPage


class TestPageMetadata(TestCase):
    def make_config(self):
        config = RawConfigParser()
        config.add_section("Comic Info")
        config.set("Comic Info", "Comic name", "Test Comic")
        return config

    def make_page(self):
        image = ComicImage(
            id="extras/story/001/page.png",
            filename="page.png",
            source_path="page.png",
            web_path="your_content/extras/story/comics/001/page.png",
            title="Image title",
            alt_text="Image hover",
            screen_reader_text="Image description",
        )
        return ComicPage(
            id="extras/story/001",
            comic_id="extras/story",
            comic_folder="extras/story/",
            page_name="001",
            page_dir="your_content/extras/story/comics/001/",
            url="/base/extras/story/comic/001/",
            title="Page title",
            post_date="2026-01-02",
            display_post_date="January 02, 2026",
            archive_post_date="January 02, 2026",
            images=[image],
            storyline="Arc 1",
            characters=["Alice"],
            tags=["mystery"],
            transcript_languages=["English"],
            extra={"Mood": "tense", "!Private": "hidden"},
        )

    def test_build_metadata_uses_versioned_resolved_shape(self):
        with patch("build.content.page_metadata.utils.BASE_DIRECTORY", "/base"):
            data = page_metadata.build_page_metadata(
                "extras/story/",
                self.make_config(),
                [self.make_page()],
                2,
                "1.1.0",
            )

        self.assertEqual(1, data["schema_version"])
        self.assertEqual("1.1.0", data["comic_git_engine_version"])
        self.assertEqual({"id": "extras/story", "name": "Test Comic"}, data["comic"])
        page = data["pages"][0]
        self.assertEqual("2026-01-02", page["post_date"])
        self.assertIsNone(page["thumbnail_url"])
        self.assertEqual({"Mood": "tense"}, page["extra"])
        self.assertEqual(
            "/base/your_content/extras/story/comics/001/page.png",
            page["images"][0]["url"],
        )
        self.assertEqual(
            {"filename", "url", "title", "alt_text", "screen_reader_text", "thumbnail_url"},
            set(page["images"][0]),
        )
        self.assertEqual("Image hover", page["images"][0]["alt_text"])
        self.assertEqual("Image description", page["images"][0]["screen_reader_text"])
        self.assertNotIn("image_index", page["images"][0])
        self.assertNotIn("configured_title", page["images"][0])

    def test_save_metadata_uses_per_comic_output_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"OUTPUT_DIR": temp_dir}, clear=False):
                path = page_metadata.save_page_metadata(
                    "extras/story/",
                    self.make_config(),
                    [self.make_page()],
                    0,
                    "1.1.0",
                )
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

        self.assertTrue(path.replace("\\", "/").endswith("extras/story/comic/page_info_list.json"))
        self.assertEqual("extras/story/001", data["pages"][0]["id"])

    def test_schema_is_draft_2020_12_and_matches_contract_fields(self):
        schema_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "schemas",
            "page_info_list.schema.json",
        )
        with open(os.path.normpath(schema_path), encoding="utf-8") as f:
            schema = json.load(f)

        self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
        self.assertEqual(
            "https://raw.githubusercontent.com/comic-git/comic_git_engine/"
            "latest/schemas/page_info_list.schema.json",
            schema["$id"],
        )
        self.assertEqual(
            {
                "schema_version",
                "comic_git_engine_version",
                "comic",
                "scheduled_post_count",
                "pages",
            },
            set(schema["required"]),
        )
        self.assertEqual(1, schema["properties"]["schema_version"]["const"])
        post_date_schema = schema["$defs"]["page"]["properties"]["post_date"]
        self.assertEqual("string", post_date_schema["type"])
        self.assertEqual({"format": "date"}, post_date_schema["anyOf"][0])
        self.assertRegex("2026-01-02T03:04:05-08:00", post_date_schema["anyOf"][1]["pattern"])
        image_schema = schema["$defs"]["image"]
        self.assertEqual(
            {"filename", "url", "title", "alt_text", "thumbnail_url"},
            set(image_schema["required"]),
        )
        self.assertEqual("string", image_schema["properties"]["screen_reader_text"]["type"])
        self.assertNotIn("id", image_schema["properties"])
        self.assertNotIn("anchor_id", image_schema["properties"])
        self.assertNotIn("image_index", image_schema["properties"])
