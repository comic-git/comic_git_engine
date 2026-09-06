import os
import tempfile
from configparser import RawConfigParser
from unittest import TestCase
from unittest.mock import patch

from build.content import page_discovery
from build.content.page_models import ComicPage


MUT = "build.content.page_discovery."


class TestPageDiscovery(TestCase):
    def make_comic_info(self):
        comic_info = RawConfigParser()
        comic_info.add_section("Comic Settings")
        comic_info.set("Comic Settings", "Date format", "%B %d, %Y")
        comic_info.set("Comic Settings", "Timezone", "UTC")
        comic_info.set("Comic Settings", "Theme", "default")
        comic_info.add_section("Archive")
        comic_info.add_section("Transcripts")
        comic_info.set("Transcripts", "Enable transcripts", "True")
        comic_info.set("Transcripts", "Load transcripts from comic folder", "True")
        return comic_info

    def write_page(self, root, name, info_text, extra_files=None):
        page_dir = os.path.join(root, "your_content", "comics", name)
        os.makedirs(page_dir, exist_ok=True)
        with open(os.path.join(page_dir, "info.ini"), "w", encoding="utf-8") as f:
            f.write(info_text)
        for file_name, content in (extra_files or {}).items():
            path = os.path.join(page_dir, file_name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        return page_dir

    def run_discovery(self, root, comic_info, delete=False, publish_all=False):
        cwd = os.getcwd()
        try:
            os.chdir(root)
            return page_discovery.discover_pages("", comic_info, delete, publish_all)
        finally:
            os.chdir(cwd)

    def test_discover_pages_rejects_invalid_timezone(self):
        comic_info = self.make_comic_info()
        comic_info.set("Comic Settings", "Timezone", "Not/AZone")

        with self.assertRaisesRegex(ValueError, "Invalid timezone specified"):
            page_discovery.discover_pages("", comic_info, False, False)

    @patch(MUT + "run_hook", return_value=None)
    def test_discovery_builds_ordered_structured_pages_and_filters_private_extra(self, _mock_hook):
        comic_info = self.make_comic_info()
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_page(
                temp_dir,
                "b-page",
                (
                    "Post date = January 02, 2020\n"
                    "Title = Page title\n"
                    "Alt text = Page hover\n"
                    "Screen reader text = Page description\n"
                    "Characters = Alice, Bob\n"
                    "Tags = mystery, noir\n"
                    "!Draft note = hidden\n"
                    "Storyline = Arc 1\n"
                    "\n[Image first]\n"
                    "Filename = page.png\n"
                    "Title =\n"
                    "Alt text =\n"
                    "Screen reader text = Image description\n"
                ),
                {"page.png": "x", "_hidden.png": "x"},
            )
            self.write_page(
                temp_dir,
                "a-page",
                "Post date = January 02, 2020\n",
                {"a.png": "x"},
            )

            pages, scheduled_count = self.run_discovery(temp_dir, comic_info)

        self.assertEqual(0, scheduled_count)
        self.assertEqual(["a-page", "b-page"], [page.page_name for page in pages])
        self.assertEqual(["a.png"], [image.filename for image in pages[0].images])
        self.assertEqual("main/a-page/a.png", pages[0].images[0].id)
        self.assertFalse(hasattr(pages[0].images[0], "anchor_id"))
        self.assertEqual("", pages[1].images[0].title)
        self.assertEqual("", pages[1].images[0].alt_text)
        self.assertEqual("Image description", pages[1].images[0].screen_reader_text)
        self.assertEqual(["Alice", "Bob"], pages[1].characters)
        self.assertEqual(["mystery", "noir"], pages[1].tags)
        self.assertNotIn("!Draft note", pages[1].extra)
        self.assertTrue(
            all(
                isinstance(hook_call.args[2][-1], ComicPage)
                for hook_call in _mock_hook.call_args_list
            )
        )

    @patch(MUT + "run_hook", return_value=None)
    def test_screen_reader_text_falls_back_without_changing_legacy_hover_text(self, _mock_hook):
        comic_info = self.make_comic_info()
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_page(
                temp_dir,
                "legacy",
                "Post date = January 02, 2020\nAlt text = Existing description\n",
                {"page.png": "x"},
            )

            pages, _scheduled_count = self.run_discovery(temp_dir, comic_info)

        image = pages[0].images[0]
        self.assertEqual("Existing description", image.alt_text)
        self.assertEqual("Existing description", image.screen_reader_text)

    @patch(MUT + "run_hook", return_value=None)
    def test_discovery_deletes_future_posts_and_respects_flat_filenames(self, _mock_hook):
        comic_info = self.make_comic_info()
        with tempfile.TemporaryDirectory() as temp_dir:
            future_dir = self.write_page(
                temp_dir,
                "future-page",
                "Post date = January 01, 2999\n",
                {"future.png": "x"},
            )
            self.write_page(
                temp_dir,
                "named-page",
                "Post date = January 01, 2020\nFilenames = one.png, two.png\n",
                {"one.png": "x", "two.png": "x"},
            )

            pages, scheduled_count = self.run_discovery(temp_dir, comic_info, delete=True)

            self.assertFalse(os.path.exists(future_dir))

        self.assertEqual(1, scheduled_count)
        self.assertEqual(["one.png", "two.png"], [image.filename for image in pages[0].images])

    @patch(MUT + "run_hook", return_value=None)
    def test_discovery_reads_structured_toml_images(self, _mock_hook):
        comic_info = self.make_comic_info()
        with tempfile.TemporaryDirectory() as temp_dir:
            page_dir = os.path.join(temp_dir, "your_content", "comics", "001")
            os.makedirs(page_dir, exist_ok=True)
            with open(os.path.join(page_dir, "info.toml"), "w", encoding="utf-8") as f:
                f.write('post_date = "2020-01-02"\n')
                f.write('characters = ["Alice", "Bob"]\n')
                f.write('tags = ["mystery", "noir"]\n')
                f.write('[[images]]\nfilename = "second.png"\ntitle = "Second"\n')
                f.write('[[images]]\nfilename = "first.png"\n')
            for filename in ("first.png", "second.png"):
                with open(os.path.join(page_dir, filename), "w", encoding="utf-8") as f:
                    f.write("x")

            pages, scheduled_count = self.run_discovery(temp_dir, comic_info)

        self.assertEqual(0, scheduled_count)
        self.assertEqual(["second.png", "first.png"], [image.filename for image in pages[0].images])
        self.assertEqual("Second", pages[0].images[0].title)
        self.assertEqual(["Alice", "Bob"], pages[0].characters)

    @patch(MUT + "run_hook", return_value=None)
    def test_discovery_orders_offset_timestamps_by_instant_and_formats_local_time(self, _mock_hook):
        comic_info = self.make_comic_info()
        comic_info.set("Comic Settings", "Date format", "%Y-%m-%d %H:%M")
        with tempfile.TemporaryDirectory() as temp_dir:
            for page_name, post_date in (
                    ("earlier", "2020-01-01T10:00:00+02:00"),
                    ("later", "2020-01-01T08:30:00+00:00"),
            ):
                page_dir = os.path.join(temp_dir, "your_content", "comics", page_name)
                os.makedirs(page_dir, exist_ok=True)
                with open(os.path.join(page_dir, "info.toml"), "w", encoding="utf-8") as f:
                    f.write(f'post_date = "{post_date}"\n')

            pages, scheduled_count = self.run_discovery(temp_dir, comic_info)

        self.assertEqual(0, scheduled_count)
        self.assertEqual(["earlier", "later"], [page.page_name for page in pages])
        self.assertEqual("2020-01-01 08:00", pages[0].display_post_date)
        self.assertEqual("2020-01-01T10:00:00+02:00", pages[0].post_date)

    @patch(MUT + "run_hook", return_value=None)
    def test_discovery_rejects_duplicate_normalized_and_escaping_paths(self, _mock_hook):
        comic_info = self.make_comic_info()
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_page(
                temp_dir,
                "duplicate",
                (
                    "Post date = January 01, 2020\n"
                    "\n[Image first]\nFilename = panels/page.png\n"
                    "\n[Image second]\nFilename = panels\\page.png\n"
                ),
                {"panels/page.png": "x"},
            )
            with self.assertRaisesRegex(ValueError, "Duplicate comic image"):
                self.run_discovery(temp_dir, comic_info)

        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_page(
                temp_dir,
                "alias",
                (
                    "Post date = January 01, 2020\n"
                    "\n[Image first]\nFilename = page.png\n"
                    "\n[Image second]\nFilename = panels/../page.png\n"
                ),
                {"page.png": "x"},
            )
            with self.assertRaisesRegex(ValueError, "Duplicate comic image"):
                self.run_discovery(temp_dir, comic_info)

        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_page(
                temp_dir,
                "escape",
                "Post date = January 01, 2020\nFilename = ../outside.png\n",
            )
            with open(os.path.join(temp_dir, "your_content", "comics", "outside.png"), "w", encoding="utf-8") as f:
                f.write("x")
            with self.assertRaisesRegex(ValueError, "must stay inside"):
                self.run_discovery(temp_dir, comic_info)
