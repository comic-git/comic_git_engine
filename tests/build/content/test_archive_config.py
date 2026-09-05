from configparser import RawConfigParser
from unittest import TestCase

from build.content import site_config
from build.content.page_models import ArchiveEntryMode, ImageTitleFallback


class TestArchiveConfig(TestCase):
    def make_config(self) -> RawConfigParser:
        config = RawConfigParser()
        config.add_section("Archive")
        return config

    def test_defaults_preserve_page_archive_behavior(self):
        config = self.make_config()

        self.assertEqual(ArchiveEntryMode.PAGES, site_config.get_archive_entry_mode(config))
        self.assertEqual(ImageTitleFallback.PAGE_TITLE, site_config.get_image_title_fallback(config))

    def test_list_images_separately_enables_image_archive_mode(self):
        config = self.make_config()
        config.set("Archive", "List images separately", "true")
        config.set("Archive", "Image title fallback", "page_title")

        self.assertEqual(ArchiveEntryMode.IMAGES, site_config.get_archive_entry_mode(config))
        self.assertEqual(ImageTitleFallback.PAGE_TITLE, site_config.get_image_title_fallback(config))

    def test_invalid_values_fail_near_config_boundary(self):
        config = self.make_config()
        config.set("Archive", "List images separately", "sometimes")
        with self.assertRaisesRegex(ValueError, "List images separately"):
            site_config.get_archive_entry_mode(config)

        config.set("Archive", "List images separately", "False")
        config.set("Archive", "Image title fallback", "random")
        with self.assertRaisesRegex(ValueError, "Image title fallback"):
            site_config.get_image_title_fallback(config)
