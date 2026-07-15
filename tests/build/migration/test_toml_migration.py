import os
import tempfile
from collections import OrderedDict
from unittest import TestCase

from build.content import page_sources
from build.migration import toml_migration


class TestTomlMigration(TestCase):
    def write_main_comic_info(self, root: str, extra_comics: str = "") -> None:
        content_dir = os.path.join(root, "your_content")
        os.makedirs(content_dir, exist_ok=True)
        with open(os.path.join(content_dir, "comic_info.ini"), "w", encoding="utf-8") as f:
            f.write("[Comic Info]\n")
            f.write("Comic name = Test Comic\n")
            f.write("Author = Test Author\n")
            f.write("Description = Test Description\n")
            f.write("\n[Comic Settings]\n")
            f.write("Date format = %B %d, %Y\n")
            f.write(f"Extra comics = {extra_comics}\n")
            f.write("\n[Transcripts]\n")
            f.write("Enable transcripts = True\n")
            f.write("Load transcripts from comic folder = True\n")
            f.write("Default language = English\n")

    def write_extra_comic_info(self, root: str, comic_folder: str) -> None:
        content_dir = os.path.join(root, "your_content", comic_folder)
        os.makedirs(content_dir, exist_ok=True)
        with open(os.path.join(content_dir, "comic_info.ini"), "w", encoding="utf-8") as f:
            f.write("[Comic Info]\n")
            f.write("Comic name = Extra Comic\n")

    def write_page(self, root: str, comic_folder: str, page_name: str) -> str:
        page_dir = os.path.join(root, "your_content", comic_folder, "comics", page_name)
        os.makedirs(page_dir, exist_ok=True)
        with open(os.path.join(page_dir, "info.ini"), "w", encoding="utf-8") as f:
            f.write("Post date = January 02, 2024\n")
            f.write("Title = Chapter One\n")
            f.write("Alt text = Alt words\n")
            f.write("Storyline = Arc 1\n")
            f.write("Characters = Alice, Bob\n")
            f.write("Tags = noir, mystery\n")
            f.write("Mood = tense\n")
            f.write("!Private = hidden\n")
        with open(os.path.join(page_dir, "second.png"), "w", encoding="utf-8") as f:
            f.write("x")
        with open(os.path.join(page_dir, "first.png"), "w", encoding="utf-8") as f:
            f.write("x")
        with open(os.path.join(page_dir, "post.txt"), "w", encoding="utf-8") as f:
            f.write("Page body")
        with open(os.path.join(page_dir, "English.md"), "w", encoding="utf-8") as f:
            f.write("**Transcript**")
        with open(os.path.join(page_dir, "social_media.json"), "w", encoding="utf-8") as f:
            f.write('{"comic": {"og:title": "Override"}}')
        return page_dir

    def run_in_host(self, root: str, callback):
        cwd = os.getcwd()
        try:
            os.chdir(root)
            return callback()
        finally:
            os.chdir(cwd)

    def test_dry_run_reports_page_without_writing_toml(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_main_comic_info(temp_dir)
            page_dir = self.write_page(temp_dir, "", "001")

            report = self.run_in_host(temp_dir, lambda: toml_migration.run_page_migration(write=False))

            self.assertEqual(1, len(report.planned))
            self.assertEqual(0, len(report.written))
            self.assertFalse(os.path.exists(os.path.join(page_dir, "info.toml")))

    def test_write_creates_page_toml_from_legacy_sources(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_main_comic_info(temp_dir)
            page_dir = self.write_page(temp_dir, "", "001")

            report = self.run_in_host(temp_dir, lambda: toml_migration.run_page_migration(write=True))

            toml_path = os.path.join(page_dir, "info.toml")
            self.assertEqual(1, len(report.written))
            self.assertTrue(os.path.exists(toml_path))
            with open(toml_path, "r", encoding="utf-8") as f:
                toml_text = f.read()
            loaded = page_sources.load_page_source_from_toml(toml_path)
            self.assertEqual("2024-01-02", loaded.post_date)
            self.assertEqual(["first.png", "second.png"], loaded.images)
            self.assertEqual("Chapter One", loaded.title)
            self.assertEqual("Page body", loaded.post_text)
            self.assertEqual(["Alice", "Bob"], loaded.characters)
            self.assertEqual(["noir", "mystery"], loaded.tags)
            self.assertEqual(OrderedDict({"English": "**Transcript**"}), loaded.transcripts)
            self.assertEqual({"og:title": "Override"}, loaded.social_media)
            self.assertEqual(OrderedDict({"Mood": "tense"}), loaded.extra)
            self.assertNotIn("Private", toml_text)

    def test_existing_toml_is_skipped_without_overwrite(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_main_comic_info(temp_dir)
            page_dir = self.write_page(temp_dir, "", "001")
            toml_path = os.path.join(page_dir, "info.toml")
            with open(toml_path, "w", encoding="utf-8") as f:
                f.write("# existing\n")

            report = self.run_in_host(temp_dir, lambda: toml_migration.run_page_migration(write=True))

            self.assertEqual(0, len(report.written))
            self.assertEqual(1, len(report.skipped))
            with open(toml_path, "r", encoding="utf-8") as f:
                self.assertEqual("# existing\n", f.read())

    def test_extra_comics_are_included_by_default(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_main_comic_info(temp_dir, "extras/story")
            self.write_extra_comic_info(temp_dir, "extras/story")
            self.write_page(temp_dir, "extras/story", "bonus")

            report = self.run_in_host(temp_dir, lambda: toml_migration.run_page_migration(write=False))

            self.assertEqual(["extras/story/"], [target.comic_folder for target in report.planned])
            self.assertTrue(report.planned[0].toml_info_path.endswith("your_content/extras/story/comics/bonus/info.toml"))

    def test_delete_legacy_removes_page_scoped_files_after_write(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_main_comic_info(temp_dir)
            page_dir = self.write_page(temp_dir, "", "001")

            report = self.run_in_host(
                temp_dir,
                lambda: toml_migration.run_page_migration(write=True, delete_legacy=True),
            )

            self.assertEqual(1, len(report.written))
            self.assertTrue(os.path.exists(os.path.join(page_dir, "info.toml")))
            self.assertFalse(os.path.exists(os.path.join(page_dir, "info.ini")))
            self.assertFalse(os.path.exists(os.path.join(page_dir, "post.txt")))
            self.assertFalse(os.path.exists(os.path.join(page_dir, "English.md")))
            self.assertFalse(os.path.exists(os.path.join(page_dir, "social_media.json")))
            self.assertTrue(os.path.exists(os.path.join(page_dir, "first.png")))
            self.assertTrue(os.path.exists(os.path.join(page_dir, "second.png")))
            self.assertEqual(
                [
                    "your_content/comics/001/English.md",
                    "your_content/comics/001/info.ini",
                    "your_content/comics/001/post.txt",
                    "your_content/comics/001/social_media.json",
                ],
                sorted(report.deleted_legacy_files),
            )

    def test_delete_legacy_cleans_already_migrated_page(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_main_comic_info(temp_dir)
            page_dir = self.write_page(temp_dir, "", "001")
            with open(os.path.join(page_dir, "info.toml"), "w", encoding="utf-8") as f:
                f.write('post_date = "2024-01-02"\nimages = ["first.png"]\n')

            report = self.run_in_host(
                temp_dir,
                lambda: toml_migration.run_page_migration(write=False, delete_legacy=True),
            )

            self.assertEqual(0, len(report.written))
            self.assertEqual(1, len(report.skipped))
            self.assertFalse(os.path.exists(os.path.join(page_dir, "info.ini")))
            self.assertFalse(os.path.exists(os.path.join(page_dir, "post.txt")))
            self.assertFalse(os.path.exists(os.path.join(page_dir, "English.md")))
            self.assertFalse(os.path.exists(os.path.join(page_dir, "social_media.json")))
            self.assertTrue(os.path.exists(os.path.join(page_dir, "info.toml")))
            self.assertEqual(4, len(report.deleted_legacy_files))
