import os
import tempfile
from configparser import RawConfigParser
from unittest import TestCase
from unittest.mock import patch

from build import site_output


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

    @patch("build.site_output.delete_output_file_space")
    def test_setup_output_file_space_delegates_to_delete(self, mock_delete_output_file_space):
        comic_info = self.make_comic_info()

        site_output.setup_output_file_space(comic_info)

        mock_delete_output_file_space.assert_called_once_with(comic_info)

    @patch("build.site_output.shutil.copy")
    @patch("build.site_output.shutil.copytree")
    def test_copy_output_assets_only_runs_when_output_dir_is_set(self, mock_copytree, mock_copy):
        site_output.copy_output_assets("")
        mock_copytree.assert_not_called()
        mock_copy.assert_not_called()

        site_output.copy_output_assets("output")

        self.assertEqual(3, mock_copytree.call_count)
        mock_copy.assert_called_once_with("favicon.ico", "output")
