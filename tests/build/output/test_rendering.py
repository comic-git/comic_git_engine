import os
from configparser import RawConfigParser
from unittest import TestCase
from unittest.mock import patch

from build.content.page_models import ComicImage, ComicPage
from build.output import rendering


MUT = "build.output.rendering."


class TestRendering(TestCase):
    def make_comic_info(self):
        comic_info = RawConfigParser()
        comic_info.add_section("Comic Settings")
        comic_info.set("Comic Settings", "Theme", "theme-name")
        return comic_info

    def make_page(self, name="001", characters=None, tags=None):
        image = ComicImage(
            id=f"main/{name}/page.png",
            filename="page.png",
            source_path="page.png",
            web_path=f"your_content/comics/{name}/page.png",
            anchor_id="comic-image-" + "a" * 64,
            title="Image",
            alt_text="Alt",
        )
        return ComicPage(
            id=f"main/{name}",
            comic_id="main",
            comic_folder="",
            page_name=name,
            page_dir=f"your_content/comics/{name}/",
            url=f"/comic/{name}/",
            title=f"Page {name}",
            post_date="2024-01-01",
            display_post_date="January 01, 2024",
            archive_post_date="January 01, 2024",
            images=[image],
            characters=characters or [],
            tags=tags or [],
        )

    @patch(MUT + "utils.write_to_template")
    @patch(MUT + "utils.get_social_media_data", side_effect=lambda *_args, **_kwargs: {"path": _args[3]})
    @patch(MUT + "get_pages_list", return_value=[
        {"template_name": "index", "title": ""},
        {"template_name": "latest", "title": "Latest Page"},
        {"template_name": "tagged", "title": ""},
    ])
    @patch(MUT + "write_tagged_pages")
    def test_write_other_pages_uses_structured_page_context(
            self,
            mock_write_tagged_pages,
            _mock_get_pages_list,
            _mock_social_media,
            mock_write_to_template,
    ):
        page = self.make_page()

        rendering.write_other_pages(
            "extras/story",
            self.make_comic_info(),
            [page],
            {"comic_url": "https://example.com"},
        )

        mock_write_tagged_pages.assert_called_once()
        self.assertEqual(2, mock_write_to_template.call_count)
        index_context = mock_write_to_template.call_args_list[0].args[2]
        self.assertEqual(page.images, index_context["images"])
        self.assertEqual("Page 001", index_context["_title"])
        self.assertEqual("Latest Page", mock_write_to_template.call_args_list[1].args[2]["_title"])

    @patch(MUT + "utils.write_to_template")
    @patch(MUT + "utils.get_social_media_data", return_value={"x": 1})
    @patch(MUT + "get_pages_list", return_value=[
        {"template_name": "latest", "title": ""},
        {"template_name": "index", "title": ""},
    ])
    def test_write_other_pages_uses_empty_defaults_and_skips_latest(
            self,
            _mock_get_pages_list,
            _mock_social_media,
            mock_write_to_template,
    ):
        rendering.write_other_pages(
            "",
            self.make_comic_info(),
            [],
            {"comic_url": "https://example.com"},
        )

        self.assertEqual(1, mock_write_to_template.call_count)
        self.assertEqual("Index", mock_write_to_template.call_args.args[2]["_title"])

    @patch(MUT + "utils.write_to_template")
    @patch(MUT + "utils.get_social_media_data", return_value={"x": 1})
    def test_write_tagged_pages_groups_structured_page_tags(self, _mock_social, mock_write):
        pages = [
            self.make_page("001", ["Alice"], ["mystery"]),
            self.make_page("002", ["Alice", "Bob"], ["action"]),
        ]

        rendering.write_tagged_pages(self.make_comic_info(), pages, {"comic_url": "https://example.com"})

        self.assertEqual(
            [
                "tagged/Alice/index.html",
                "tagged/mystery/index.html",
                "tagged/Bob/index.html",
                "tagged/action/index.html",
            ],
            [call.args[1] for call in mock_write.call_args_list],
        )

    @patch(MUT + "run_hook")
    @patch(MUT + "write_other_pages")
    @patch(MUT + "utils.write_to_template")
    @patch(MUT + "utils.get_social_media_data", return_value={"card": "ok"})
    @patch(MUT + "utils.build_markdown_parser")
    @patch(MUT + "utils.build_jinja_environment")
    def test_write_html_files_uses_structured_context_and_theme_precedence(
            self,
            mock_build_jinja_environment,
            _mock_markdown,
            _mock_social,
            mock_write,
            mock_write_other,
            mock_hook,
    ):
        page = self.make_page()
        global_values = {"theme": "theme-name", "comic_url": "https://example.com"}
        comic_info = self.make_comic_info()

        rendering.write_html_files(
            "extras/story/",
            comic_info,
            [page],
            global_values,
        )

        mock_build_jinja_environment.assert_called_once_with(
            comic_info,
            [
                "your_content/themes/theme-name/templates/extras/story/",
                "your_content/themes/theme-name/templates",
                "comic_git_engine/templates",
            ],
        )
        self.assertEqual("extras/story/comic/001/index.html", mock_write.call_args.args[1])
        context = mock_write.call_args.args[2]
        self.assertEqual(page.images, context["images"])
        self.assertNotIn("comic_paths", context)
        mock_write_other.assert_called_once()
        mock_hook.assert_called_once_with(
            "theme-name",
            "build_other_pages",
            ["extras/story/", comic_info, [page]],
        )

    def test_templates_reference_structured_images_and_archive_entries(self):
        with open("templates/comic.tpl", encoding="utf-8") as f:
            comic_template = f.read()
        with open("templates/archive.tpl", encoding="utf-8") as f:
            archive_template = f.read()
        with open("templates/infinite_scroll.tpl", encoding="utf-8") as f:
            infinite_scroll_template = f.read()
        with open("js/infinite_scroll.js", encoding="utf-8") as f:
            infinite_scroll_script = f.read()

        self.assertIn("image.anchor_id", comic_template)
        self.assertIn('alt="{{ image.alt_text | e }}"', comic_template)
        self.assertNotIn("comic_paths", comic_template)
        self.assertIn("entry.page_url", archive_template)
        self.assertIn("archive-thumbnail-text-only", archive_template)
        self.assertIn('json["pages"]', infinite_scroll_script)
        self.assertIn('page["images"]', infinite_scroll_script)
        self.assertIn('image["anchor_id"]', infinite_scroll_script)
        self.assertIn('image_node.alt = image["alt_text"]', infinite_scroll_script)
        self.assertNotIn("image_file_names", infinite_scroll_script)
        self.assertIn('load_page("{{ comic_base_dir }}")', infinite_scroll_template)
