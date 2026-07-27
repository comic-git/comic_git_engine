import os
import tempfile
from configparser import RawConfigParser
from unittest import TestCase
from unittest.mock import patch

from build.content import comic_data
from build.content.page_models import ComicImage, ComicPage


MUT = "build.content.comic_data."


class TestComicData(TestCase):
    def make_comic_info(self):
        comic_info = RawConfigParser()
        comic_info.add_section("Comic Settings")
        comic_info.set("Comic Settings", "Theme", "default")
        comic_info.add_section("Archive")
        comic_info.set("Archive", "Date format", "%Y-%m-%d")
        return comic_info

    def make_page(self, name="001", post_md="main body"):
        image = ComicImage(
            id=f"main/{name}/page.png",
            filename="page.png",
            source_path="page.png",
            web_path=f"your_content/comics/{name}/page.png",
            anchor_id="comic-image-id",
            title="Chapter One",
            alt_text="Alt",
        )
        return ComicPage(
            id=f"main/{name}",
            comic_id="main",
            comic_folder="",
            page_name=name,
            page_dir=f"your_content/comics/{name}/",
            url=f"/comic/{name}/",
            title="Chapter One",
            post_date="2024-01-02",
            display_post_date="January 02, 2024",
            archive_post_date="January 02, 2024",
            images=[image],
            post_md=post_md,
            extra={"Mood": "tense"},
        )

    def test_format_user_variable_preserves_page_name_and_normalizes_other_keys(self):
        self.assertEqual("_post_date", comic_data.format_user_variable("Post date"))
        self.assertEqual(
            "_this_page_is_full_of_spiders_1",
            comic_data.format_user_variable("This page is full of spiders!!1"),
        )
        self.assertEqual("page_name", comic_data.format_user_variable("page_name"))

    def test_get_ids_handles_first_middle_and_last_pages(self):
        pages = [self.make_page("001"), self.make_page("002"), self.make_page("003")]

        self.assertEqual("001", comic_data.get_ids(pages, 0)["previous_id"])
        self.assertEqual("002", comic_data.get_ids(pages, 0)["next_id"])
        self.assertEqual("003", comic_data.get_ids(pages, 2)["next_id"])

    @patch(MUT + "run_hook", return_value=None)
    def test_enrich_comic_page_adds_navigation_archive_date_and_post_wrappers(self, _mock_hook):
        comic_info = self.make_comic_info()
        page = self.make_page()
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = os.getcwd()
            content_dir = os.path.join(temp_dir, "your_content")
            os.makedirs(content_dir)
            with open(os.path.join(content_dir, "before post text.txt"), "w", encoding="utf-8") as f:
                f.write("before")
            with open(os.path.join(content_dir, "after post text.html"), "w", encoding="utf-8") as f:
                f.write("<i>after</i>")
            try:
                os.chdir(temp_dir)
                result = comic_data.enrich_comic_page(
                    "",
                    comic_info,
                    page,
                    "001",
                    "001",
                    "001",
                    "002",
                    "002",
                )
            finally:
                os.chdir(cwd)

        self.assertIs(page, result)
        self.assertEqual("2024-01-02", page.archive_post_date)
        self.assertEqual("before\n\nmain body\n\n<i>after</i>", page.post_md)
        self.assertIn("<p>before</p>", page.post_html)
        self.assertEqual("002", page.next_id)
        self.assertIs(page, _mock_hook.call_args.args[2][-1])

    @patch(MUT + "run_hook", side_effect=lambda _theme, _name, args: args[-1])
    def test_build_comic_pages_preserves_order_and_navigation(self, _mock_hook):
        pages = [self.make_page("001"), self.make_page("002")]

        result = comic_data.build_comic_pages("", self.make_comic_info(), pages)

        self.assertEqual(["001", "002"], [page.page_name for page in result])
        self.assertEqual("002", result[0].next_id)
        self.assertEqual("001", result[1].previous_id)

    def test_template_context_exposes_structured_images_without_legacy_image_fields(self):
        page = self.make_page()
        page.first_id = page.previous_id = page.next_id = page.last_id = "001"

        context = comic_data.page_to_template_context(page)

        self.assertEqual(page.images, context["images"])
        self.assertEqual("tense", context["_mood"])
        self.assertNotIn("image_file_names", context)
        self.assertNotIn("comic_paths", context)
        self.assertNotIn("escaped_alt_text", context)
        self.assertNotIn("thumbnail_path", context)
