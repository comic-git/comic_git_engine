import os
import tempfile
from configparser import RawConfigParser
from unittest import TestCase

from build.content import comic_config_sources


class TestComicConfigSources(TestCase):
    def write_toml(self, text: str) -> str:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = os.path.join(temp_dir.name, "comic_info.toml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def test_load_comic_config_from_toml_maps_scalars_lists_and_booleans(self):
        path = self.write_toml(
            """
[comic]
name = "Test Comic"
author = "Test Author"
description = "Test Description"

[engine]
version = "1.1"

[site]
theme = "custom"
date_format = "%Y-%m-%d"
timezone = "UTC"
extra_comics = ["extras/story", "bonus"]
markdown_extras = ["tables", "fenced-code-blocks"]

[archive]
use_thumbnails = true
list_images_separately = true
image_title_fallback = "filename"
show_text_only_posts = false

[image_processing]
create_thumbnails = true
overwrite_existing_images = true
thumbnail_size = "200x200"

[rss]
build = true
newest_first = false
image_width = "144"
channel_description = "Feed Description"
"""
        )

        comic_info = comic_config_sources.load_comic_config_from_toml(path)

        self.assertEqual("Test Comic", comic_info.get("Comic Info", "Comic name"))
        self.assertEqual("Test Author", comic_info.get("Comic Info", "Author"))
        self.assertEqual("1.1", comic_info.get("Comic Settings", "Engine version"))
        self.assertEqual("custom", comic_info.get("Comic Settings", "Theme"))
        self.assertEqual("extras/story, bonus", comic_info.get("Comic Settings", "Extra comics"))
        self.assertEqual("tables, fenced-code-blocks", comic_info.get("Comic Settings", "Markdown extras"))
        self.assertTrue(comic_info.getboolean("Archive", "Use thumbnails"))
        self.assertTrue(comic_info.getboolean("Archive", "List images separately"))
        self.assertEqual("filename", comic_info.get("Archive", "Image title fallback"))
        self.assertFalse(comic_info.getboolean("Archive", "Show text-only posts"))
        self.assertTrue(comic_info.getboolean("Image Reprocessing", "Create thumbnails"))
        self.assertTrue(comic_info.getboolean("Image Reprocessing", "Overwrite existing images"))
        self.assertEqual("200x200", comic_info.get("Image Reprocessing", "Thumbnail size"))
        self.assertTrue(comic_info.getboolean("RSS Feed", "Build RSS feed"))
        self.assertFalse(comic_info.getboolean("RSS Feed", "Newest first"))
        self.assertEqual("144", comic_info.get("RSS Feed", "Image width"))
        self.assertEqual("Feed Description", comic_info.get("RSS Feed", "Description"))

    def test_load_comic_config_from_toml_keeps_sparse_optional_values_omitted(self):
        path = self.write_toml(
            """
[comic]
name = "Test Comic"

[site]
date_format = "%B %d, %Y"
"""
        )

        comic_info = comic_config_sources.load_comic_config_from_toml(path)

        self.assertEqual("Test Comic", comic_info.get("Comic Info", "Comic name"))
        self.assertEqual("%B %d, %Y", comic_info.get("Comic Settings", "Date format"))
        self.assertFalse(comic_info.has_option("Comic Settings", "Theme"))
        self.assertFalse(comic_info.has_option("RSS Feed", "Build RSS feed"))

    def test_load_comic_config_from_toml_maps_links_pages_and_webring(self):
        path = self.write_toml(
            """
[webring]
enabled = true
endpoint = "local"
id = "comic_a"
show_all_members = true
exclude_own_comic_from_members = false

[[links]]
name = "About"
url = "/about/"

[[links]]
image_url = "cdn.example.com/button.png"
url = "https://example.com/"
open_in_new_tab = true

[[pages]]
template_name = "about"
title = "About"

[[pages]]
template_name = "cast"
title = "Cast"
"""
        )

        comic_info = comic_config_sources.load_comic_config_from_toml(path)

        self.assertEqual("/about/", comic_info.get("Links Bar", "About"))
        self.assertEqual("^https://example.com/", comic_info.get("Links Bar", "cdn.example.com/button.png"))
        self.assertEqual("About", comic_info.get("Pages", "about"))
        self.assertEqual("Cast", comic_info.get("Pages", "cast"))
        self.assertTrue(comic_info.getboolean("Webring", "Enable webring"))
        self.assertEqual("local", comic_info.get("Webring", "Endpoint"))
        self.assertEqual("comic_a", comic_info.get("Webring", "Webring ID"))
        self.assertTrue(comic_info.getboolean("Webring", "Show all members"))
        self.assertFalse(comic_info.getboolean("Webring", "Exclude own comic from members"))

    def test_load_comic_config_from_toml_rejects_bad_list_type(self):
        path = self.write_toml(
            """
[site]
extra_comics = "extras/story"
"""
        )

        with self.assertRaisesRegex(ValueError, "site.extra_comics"):
            comic_config_sources.load_comic_config_from_toml(path)

    def test_load_comic_config_from_toml_rejects_malformed_link(self):
        path = self.write_toml(
            """
[[links]]
name = "About"
image_url = "button.png"
url = "/about/"
"""
        )

        with self.assertRaisesRegex(ValueError, "links\\[0\\]"):
            comic_config_sources.load_comic_config_from_toml(path)

    def test_load_comic_config_from_toml_rejects_unknown_top_level_key(self):
        path = self.write_toml(
            """
[mystery]
value = "ignored"
"""
        )

        with self.assertRaisesRegex(ValueError, "Unsupported key mystery in comic_info.toml"):
            comic_config_sources.load_comic_config_from_toml(path)

    def test_load_comic_config_from_toml_rejects_unknown_engine_table_key(self):
        path = self.write_toml(
            """
[site]
timezome = "UTC"
"""
        )

        with self.assertRaisesRegex(ValueError, "Unsupported key site.timezome in comic_info.toml"):
            comic_config_sources.load_comic_config_from_toml(path)

    def test_load_comic_config_from_toml_rejects_removed_allow_missing_variables_option(self):
        path = self.write_toml(
            """
[site]
allow_missing_variables_in_templates = true
"""
        )

        with self.assertRaisesRegex(
                ValueError,
                "Unsupported key site.allow_missing_variables_in_templates in comic_info.toml",
        ):
            comic_config_sources.load_comic_config_from_toml(path)

    def test_load_comic_config_from_toml_rejects_unknown_link_key(self):
        path = self.write_toml(
            """
[[links]]
name = "About"
url = "/about/"
label = "ignored"
"""
        )

        with self.assertRaisesRegex(ValueError, "Unsupported key links\\[0\\].label in comic_info.toml"):
            comic_config_sources.load_comic_config_from_toml(path)

    def test_load_comic_config_from_toml_rejects_unknown_page_key(self):
        path = self.write_toml(
            """
[[pages]]
template_name = "about"
title = "About"
slug = "ignored"
"""
        )

        with self.assertRaisesRegex(ValueError, "Unsupported key pages\\[0\\].slug in comic_info.toml"):
            comic_config_sources.load_comic_config_from_toml(path)

    def test_load_comic_config_from_toml_rejects_legacy_scalar_collision(self):
        path = self.write_toml(
            """
[comic]
name = "First Class"

[legacy."Comic Info"]
"Comic name" = "Legacy Override"
"""
        )

        with self.assertRaisesRegex(
                ValueError,
                'legacy\\["Comic Info"\\]\\["Comic name"\\].*comic.name',
        ):
            comic_config_sources.load_comic_config_from_toml(path)

    def test_load_comic_config_from_toml_rejects_legacy_link_collision(self):
        path = self.write_toml(
            """
[[links]]
name = "About"
url = "/about/"

[legacy."Links Bar"]
About = "/legacy-about/"
"""
        )

        with self.assertRaisesRegex(ValueError, 'legacy\\["Links Bar"\\]\\["About"\\].*links\\[0\\]'):
            comic_config_sources.load_comic_config_from_toml(path)

    def test_load_comic_config_from_toml_rejects_legacy_page_collision(self):
        path = self.write_toml(
            """
[[pages]]
template_name = "about"
title = "About"

[legacy.Pages]
about = "Legacy About"
"""
        )

        with self.assertRaisesRegex(ValueError, 'legacy\\["Pages"\\]\\["about"\\].*pages\\[0\\]'):
            comic_config_sources.load_comic_config_from_toml(path)

    def test_legacy_parser_serializes_to_sparse_toml_and_round_trips(self):
        comic_info = RawConfigParser()
        comic_info.optionxform = str
        comic_info.add_section("Comic Info")
        comic_info.set("Comic Info", "Comic name", "Test Comic")
        comic_info.add_section("Comic Settings")
        comic_info.set("Comic Settings", "Engine version", "master")
        comic_info.set("Comic Settings", "Extra comics", "extras/story, bonus")
        comic_info.add_section("Links Bar")
        comic_info.set("Links Bar", "About", "/about/")
        comic_info.set("Links Bar", "cdn.example.com/button.png", "^https://example.com/")
        comic_info.add_section("Pages")
        comic_info.set("Pages", "cast", "Cast")
        comic_info.add_section("Custom Section")
        comic_info.set("Custom Section", "Custom Option", "Custom Value")
        comic_info.add_section("Archive")
        comic_info.set("Archive", "Show text-only posts", "False")
        comic_info.add_section("RSS Feed")
        comic_info.set("RSS Feed", "Description", "Feed Description")

        toml_text = comic_config_sources.serialize_comic_config_to_toml(comic_info)
        path = self.write_toml(toml_text)

        loaded = comic_config_sources.load_comic_config_from_toml(path)
        self.assertEqual("Test Comic", loaded.get("Comic Info", "Comic name"))
        self.assertEqual("master", loaded.get("Comic Settings", "Engine version"))
        self.assertEqual("extras/story, bonus", loaded.get("Comic Settings", "Extra comics"))
        self.assertEqual("/about/", loaded.get("Links Bar", "About"))
        self.assertEqual("^https://example.com/", loaded.get("Links Bar", "cdn.example.com/button.png"))
        self.assertEqual("Cast", loaded.get("Pages", "cast"))
        self.assertEqual("Custom Value", loaded.get("Custom Section", "Custom Option"))
        self.assertFalse(loaded.getboolean("Archive", "Show text-only posts"))
        self.assertEqual("Feed Description", loaded.get("RSS Feed", "Description"))
        self.assertIn("show_text_only_posts = false", toml_text)
        self.assertIn('channel_description = "Feed Description"', toml_text)
        self.assertIn("[engine]", toml_text)
        self.assertIn('version = "master"', toml_text)
        self.assertNotIn('"Engine version"', toml_text)

    def test_removed_allow_missing_variables_option_is_preserved_as_legacy_migration_data(self):
        comic_info = RawConfigParser()
        comic_info.optionxform = str
        comic_info.add_section("Comic Settings")
        comic_info.set("Comic Settings", "Allow missing variables in templates", "True")

        toml_text = comic_config_sources.serialize_comic_config_to_toml(comic_info)

        self.assertIn('[legacy."Comic Settings"]', toml_text)
        self.assertIn('"Allow missing variables in templates" = "True"', toml_text)
