import os
import tempfile
from unittest import TestCase

from build.content import page_models


class TestPageModels(TestCase):
    def test_comic_and_image_ids_are_normalized_and_comic_aware(self):
        main_id = page_models.build_image_id("", "001", r"panels\page one.png")
        extra_id = page_models.build_image_id("extras\\story\\", "001", r"panels\page one.png")

        self.assertEqual("main/001/panels/page one.png", main_id)
        self.assertEqual("extras/story/001/panels/page one.png", extra_id)

    def test_image_keeps_internal_identity_without_a_public_anchor_field(self):
        image = page_models.ComicImage(
            id="main/001/page.png",
            filename="page.png",
            source_path="page.png",
            web_path="your_content/comics/001/page.png",
            title="Page",
            alt_text="Alt",
        )

        self.assertEqual("main/001/page.png", image.id)
        self.assertFalse(hasattr(image, "anchor_id"))

    def test_page_title_uses_configured_title_then_first_filename_then_page_name(self):
        self.assertEqual(
            "Explicit",
            page_models.resolve_page_title("Explicit", ["first.png", "second.png"], "001"),
        )
        self.assertEqual(
            "first",
            page_models.resolve_page_title(None, ["panels/first.png", "second.png"], "001"),
        )
        self.assertEqual("001", page_models.resolve_page_title("   ", [], "001"))

    def test_image_title_page_mode_uses_explicit_page_title_then_own_filename(self):
        self.assertEqual(
            "Page title",
            page_models.resolve_image_title(
                None,
                "Page title",
                "second.png",
                page_models.ImageTitleFallback.PAGE_TITLE,
            ),
        )
        self.assertEqual(
            "second",
            page_models.resolve_image_title(
                None,
                None,
                "second.png",
                page_models.ImageTitleFallback.PAGE_TITLE,
            ),
        )

    def test_image_title_filename_mode_uses_filename_before_page_title(self):
        self.assertEqual(
            "second",
            page_models.resolve_image_title(
                None,
                "Page title",
                "second.png",
                page_models.ImageTitleFallback.FILENAME,
            ),
        )

    def test_present_blank_image_title_and_alt_text_are_respected(self):
        self.assertEqual(
            "",
            page_models.resolve_image_title(
                "",
                "Page title",
                "second.png",
                page_models.ImageTitleFallback.PAGE_TITLE,
            ),
        )
        self.assertEqual("", page_models.resolve_image_alt_text("", "Page alt"))

    def test_omitted_image_alt_text_inherits_page_alt_text(self):
        self.assertEqual("Page alt", page_models.resolve_image_alt_text(None, "Page alt"))
        self.assertEqual("", page_models.resolve_image_alt_text(None, None))

    def test_validate_page_asset_normalizes_separators_and_allows_nested_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_dir = os.path.join(temp_dir, "panels")
            os.makedirs(nested_dir)
            with open(os.path.join(nested_dir, "page.png"), "w", encoding="utf-8") as f:
                f.write("x")

            filename, source_path = page_models.validate_page_asset_path(
                temp_dir,
                r"panels\page.png",
                "comic image",
            )

        self.assertEqual("panels/page.png", filename)
        self.assertTrue(source_path.replace("\\", "/").endswith("/panels/page.png"))

    def test_validate_page_asset_rejects_traversal_absolute_paths_and_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            outside = os.path.join(os.path.dirname(temp_dir), "outside.png")
            with open(outside, "w", encoding="utf-8") as f:
                f.write("x")
            self.addCleanup(lambda: os.path.exists(outside) and os.remove(outside))
            os.makedirs(os.path.join(temp_dir, "directory"))

            with self.assertRaisesRegex(ValueError, "must stay inside"):
                page_models.validate_page_asset_path(temp_dir, "../outside.png", "comic image")
            with self.assertRaisesRegex(ValueError, "must be relative"):
                page_models.validate_page_asset_path(temp_dir, outside, "comic image")
            with self.assertRaisesRegex(ValueError, "must be a file"):
                page_models.validate_page_asset_path(temp_dir, "directory", "comic image")

    def test_validate_unique_filenames_rejects_normalized_duplicates(self):
        with self.assertRaisesRegex(ValueError, "Duplicate comic image"):
            page_models.validate_unique_filenames(["panels/page.png", r"panels\page.png"])
        with self.assertRaisesRegex(ValueError, "Duplicate comic image"):
            page_models.validate_unique_filenames(["page.png", "panels/../page.png"])
