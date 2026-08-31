from configparser import RawConfigParser
from unittest import TestCase
from unittest.mock import patch

from build.content import site_config


MUT = "build.content.site_config."


class TestSiteConfig(TestCase):

    def make_comic_info(self):
        comic_info = RawConfigParser()
        comic_info.add_section("Comic Settings")
        comic_info.add_section("Links Bar")
        comic_info.add_section("Pages")
        return comic_info

    @patch(MUT + "web_path", side_effect=lambda path: path)
    def test_get_links_list_with_text_and_image_links(self, _mock_web_path):
        comic_info = self.make_comic_info()
        comic_info.set("Links Bar", "Home", "/")
        comic_info.set("Links Bar", "/your_content/images/button.png", "^/links")
        comic_info.set("Links Bar", "cdn.example.com/button.png", "https://target.example.com")

        links = site_config.get_links_list(comic_info)

        self.assertEqual(
            [
                {
                    "name": "home",
                    "image_url": "",
                    "open_in_new_tab": False,
                    "url": "/",
                },
                {
                    "name": "",
                    "image_url": "/your_content/images/button.png",
                    "open_in_new_tab": True,
                    "url": "/links",
                },
                {
                    "name": "",
                    "image_url": "https://cdn.example.com/button.png",
                    "open_in_new_tab": False,
                    "url": "https://target.example.com",
                },
            ],
            links,
        )

    def test_get_pages_list_without_pages_section(self):
        comic_info = RawConfigParser()

        self.assertEqual([], site_config.get_pages_list(comic_info))

    def test_get_pages_list_with_multiple_pages(self):
        comic_info = self.make_comic_info()
        comic_info.set("Pages", "index", "Home")
        comic_info.set("Pages", "archive", "Archive")

        self.assertEqual(
            [
                {"template_name": "index", "title": "Home"},
                {"template_name": "archive", "title": "Archive"},
            ],
            site_config.get_pages_list(comic_info),
        )

    def test_get_extra_comics_list_handles_empty_and_csv_values(self):
        comic_info = self.make_comic_info()

        self.assertEqual([], site_config.get_extra_comics_list(comic_info))

        comic_info.set("Comic Settings", "Extra comics", "side-story, bonus/alt")
        self.assertEqual(["side-story", "bonus/alt"], site_config.get_extra_comics_list(comic_info))

    def test_get_extra_comic_info_merges_data(self):
        comic_info = self.make_comic_info()
        comic_info.add_section("Comic Info")
        comic_info.set("Comic Info", "Comic name", "Main Comic")
        comic_info.set("Links Bar", "Home", "/")
        comic_info.set("Pages", "index", "Main Home")

        def fake_load_extra_comic_info(folder_name, loaded_comic_info):
            self.assertEqual("extras/story", folder_name)
            merged = RawConfigParser()
            merged.add_section("Comic Info")
            merged.set("Comic Info", "Comic name", "Extra Comic")
            merged.add_section("Links Bar")
            merged.set("Links Bar", "Cast", "/cast")
            return merged

        with patch(MUT + "load_extra_comic_info_with_precedence", side_effect=fake_load_extra_comic_info):
            extra_info = site_config.get_extra_comic_info("extras/story", comic_info)

        self.assertEqual("Extra Comic", extra_info.get("Comic Info", "Comic name"))
        self.assertEqual("/cast", extra_info.get("Links Bar", "Cast"))

    def test_show_text_only_posts_defaults_true_and_honors_false(self):
        comic_info = self.make_comic_info()

        self.assertTrue(site_config.get_show_text_only_posts(comic_info))

        comic_info.add_section("Archive")
        comic_info.set("Archive", "Show text-only posts", "False")
        self.assertFalse(site_config.get_show_text_only_posts(comic_info))
