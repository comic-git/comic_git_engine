import ast
import os
from types import SimpleNamespace
from unittest import TestCase

from jinja2 import Environment, FileSystemLoader, StrictUndefined


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestHookExample(TestCase):
    def test_example_defines_current_hook_signatures(self):
        path = os.path.join(ROOT_DIR, "extras", "hooks.py")
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=path)

        functions = {
            node.name: [argument.arg for argument in node.args.args]
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
        }

        self.assertEqual(
            {
                "preprocess": ["comic_info"],
                "extra_page_info_processing": ["comic_folder", "comic_info", "page_path", "page"],
                "extra_comic_dict_processing": ["comic_folder", "comic_info", "page"],
                "extra_get_storylines_processing": ["comic_info", "pages", "storylines"],
                "extra_global_values": ["comic_folder", "comic_info", "pages"],
                "build_other_pages": ["comic_folder", "comic_info", "pages"],
                "postprocess": ["comic_info", "pages", "global_values"],
            },
            functions,
        )

    def test_example_describes_structured_hook_values(self):
        path = os.path.join(ROOT_DIR, "extras", "hooks.py")
        with open(path, encoding="utf-8") as f:
            source = f.read()

        self.assertIn("ComicPage", source)
        self.assertIn("ComicImage", source)
        self.assertIn("ArchiveEntry", source)
        self.assertNotIn("comic_data_dict", source)


class TestMinimalComicTemplate(TestCase):
    def render_template(self) -> str:
        environment = Environment(
            loader=FileSystemLoader([
                os.path.join(ROOT_DIR, "extras"),
                os.path.join(ROOT_DIR, "templates"),
            ]),
            undefined=StrictUndefined,
        )
        return environment.get_template("comic_minimal.tpl").render(
            base_dir="/site",
            comic_base_dir="/site",
            theme="default",
            banner_image="/site/banner.png",
            comic_title="Test Comic",
            _title="Page title",
            links=[],
            images=[SimpleNamespace(
                web_path="comic/page.png",
                alt_text="Page hover text",
                screen_reader_text="Page screen reader text",
            )],
            first_id="001",
            previous_id="001",
            current_id="002",
            next_id="003",
            last_id="004",
            first_anchor="comic-image-1",
            previous_anchor="comic-image-1",
            next_anchor="comic-image-1",
            last_anchor="comic-image-1",
            page_title="Page title",
            _post_date="January 2, 2024",
            _storyline="First arc",
            _characters=["Alice"],
            _tags=["mystery"],
            use_images_in_navigation_bar=False,
            post_html="<p>Post</p>",
            version="1.1",
        )

    def test_template_renders_current_structured_context_strictly(self):
        rendered = self.render_template()

        self.assertIn('id="comic-image-1"', rendered)
        self.assertIn('src="/site/comic/page.png"', rendered)
        self.assertIn('title="Page hover text"', rendered)
        self.assertIn('alt="Page screen reader text"', rendered)
        self.assertIn('/comic/003/#comic-image-1', rendered)
        self.assertIn('/archive/#archive-section-First-arc', rendered)
        self.assertIn('/tagged/Alice/', rendered)
        self.assertIn('/tagged/mystery/', rendered)

    def test_template_uses_only_current_essential_page_fields(self):
        path = os.path.join(ROOT_DIR, "extras", "comic_minimal.tpl")
        with open(path, encoding="utf-8") as f:
            source = f.read()

        self.assertNotIn("comic_paths", source)
        self.assertNotIn("escaped_alt_text", source)
        self.assertNotIn("#comic-page", source)
        self.assertNotIn("tagged_pages_enabled", source)
        self.assertNotIn("_on_comic_click", source)
