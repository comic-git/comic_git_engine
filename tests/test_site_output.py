import os
import tempfile
from configparser import RawConfigParser
from unittest import TestCase
from unittest.mock import patch

from build.output import site_output


class TestSiteOutput(TestCase):

    def make_comic_info(self):
        comic_info = RawConfigParser()
        comic_info.add_section("Comic Settings")
        comic_info.set("Comic Settings", "Extra comics", "extras/story")
        comic_info.add_section("Pages")
        comic_info.set("Pages", "index", "Home")
        comic_info.set("Pages", "404", "Missing")
        comic_info.set("Pages", "about", "About")
        return comic_info

    def test_delete_output_file_space_deletes_output_dir_wholesale(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = os.path.join(temp_dir, "output")
            os.makedirs(output_dir)
            with patch.dict(os.environ, {"OUTPUT_DIR": output_dir}, clear=False):
                site_output.delete_output_file_space(self.make_comic_info())

            self.assertFalse(os.path.exists(output_dir))

    def test_delete_output_file_space_defaults_to_build_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = os.getcwd()
            build_dir = os.path.join(temp_dir, "build")
            os.makedirs(build_dir)
            try:
                os.chdir(temp_dir)
                with patch.dict(os.environ, {}, clear=True):
                    site_output.delete_output_file_space(self.make_comic_info())
            finally:
                os.chdir(cwd)

            self.assertFalse(os.path.exists(build_dir))

    def test_delete_output_file_space_deletes_root_outputs_and_extra_comics(self):
        comic_info = self.make_comic_info()
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = os.getcwd()
            os.makedirs(os.path.join(temp_dir, "comic"))
            os.makedirs(os.path.join(temp_dir, "about"))
            os.makedirs(os.path.join(temp_dir, "extras", "story"))
            with open(os.path.join(temp_dir, "feed.xml"), "w", encoding="utf-8") as f:
                f.write("feed")
            with open(os.path.join(temp_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write("index")
            with open(os.path.join(temp_dir, "404.html"), "w", encoding="utf-8") as f:
                f.write("404")
            try:
                os.chdir(temp_dir)
                with patch.dict(os.environ, {"OUTPUT_DIR": ""}, clear=False):
                    site_output.delete_output_file_space(comic_info)
            finally:
                os.chdir(cwd)

            self.assertFalse(os.path.exists(os.path.join(temp_dir, "comic")))
            self.assertFalse(os.path.exists(os.path.join(temp_dir, "about")))
            self.assertFalse(os.path.exists(os.path.join(temp_dir, "extras", "story")))
            self.assertFalse(os.path.exists(os.path.join(temp_dir, "feed.xml")))
            self.assertFalse(os.path.exists(os.path.join(temp_dir, "index.html")))
            self.assertFalse(os.path.exists(os.path.join(temp_dir, "404.html")))

    @patch("build.output.site_output.delete_output_file_space")
    def test_setup_output_file_space_delegates_to_delete(self, mock_delete_output_file_space):
        comic_info = self.make_comic_info()

        site_output.setup_output_file_space(comic_info)

        mock_delete_output_file_space.assert_called_once_with(comic_info)

    @patch("build.output.site_output.shutil.copytree")
    def test_copy_output_assets_only_runs_when_output_dir_is_set(self, mock_copytree):
        site_output.copy_output_assets("")
        mock_copytree.assert_not_called()

        site_output.copy_output_assets("output")

        self.assertEqual(3, mock_copytree.call_count)

    def test_copy_site_root_files_copies_files_into_output_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = os.getcwd()
            output_dir = os.path.join(temp_dir, "build")
            site_root_dir = os.path.join(temp_dir, "your_content", "site_root")
            os.makedirs(os.path.join(site_root_dir, "nested"))
            with open(os.path.join(site_root_dir, "favicon.ico"), "w", encoding="utf-8") as f:
                f.write("icon")
            with open(os.path.join(site_root_dir, "nested", "robots.txt"), "w", encoding="utf-8") as f:
                f.write("robots")
            try:
                os.chdir(temp_dir)
                site_output.copy_site_root_files(output_dir)
            finally:
                os.chdir(cwd)

            with open(os.path.join(output_dir, "favicon.ico"), encoding="utf-8") as f:
                self.assertEqual("icon", f.read())
            with open(os.path.join(output_dir, "nested", "robots.txt"), encoding="utf-8") as f:
                self.assertEqual("robots", f.read())

    def test_copy_site_root_files_copies_files_into_repo_root_when_output_dir_blank(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = os.getcwd()
            site_root_dir = os.path.join(temp_dir, "your_content", "site_root")
            os.makedirs(site_root_dir)
            with open(os.path.join(site_root_dir, "favicon.ico"), "w", encoding="utf-8") as f:
                f.write("icon")
            try:
                os.chdir(temp_dir)
                site_output.copy_site_root_files("")
            finally:
                os.chdir(cwd)

            with open(os.path.join(temp_dir, "favicon.ico"), encoding="utf-8") as f:
                self.assertEqual("icon", f.read())

    @patch("builtins.print")
    def test_copy_site_root_files_warns_when_overwriting_existing_file(self, mock_print):
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = os.getcwd()
            output_dir = os.path.join(temp_dir, "build")
            site_root_dir = os.path.join(temp_dir, "your_content", "site_root")
            os.makedirs(site_root_dir)
            os.makedirs(output_dir)
            with open(os.path.join(site_root_dir, "favicon.ico"), "w", encoding="utf-8") as f:
                f.write("new")
            with open(os.path.join(output_dir, "favicon.ico"), "w", encoding="utf-8") as f:
                f.write("old")
            try:
                os.chdir(temp_dir)
                site_output.copy_site_root_files(output_dir)
            finally:
                os.chdir(cwd)

            mock_print.assert_any_call(
                f"WARNING: Overwriting existing output file with site_root file: {os.path.join(output_dir, 'favicon.ico')}"
            )
            with open(os.path.join(output_dir, "favicon.ico"), encoding="utf-8") as f:
                self.assertEqual("new", f.read())

    def test_copy_site_root_files_raises_when_site_root_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                with self.assertRaisesRegex(NotADirectoryError, "your_content/site_root"):
                    site_output.copy_site_root_files("build")
            finally:
                os.chdir(cwd)
