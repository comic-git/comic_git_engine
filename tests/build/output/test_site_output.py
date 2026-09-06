import os
import tempfile
from configparser import RawConfigParser
from unittest import TestCase
from unittest.mock import patch
from pathlib import Path

from build.output import site_output


MUT = "build.output.site_output."


class TestHiddenOutputPolicy(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "build"
        self.root.mkdir()
        self.write("index.html")

    def write(self, relative):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("content", encoding="utf-8")

    def files(self):
        return {p.relative_to(self.root).as_posix() for p in self.root.rglob("*") if p.is_file()}

    def test_empty_allowlist_removes_hidden_paths_at_all_depths(self):
        for path in [".htaccess", ".git/config", "assets/.secret", "assets/_thumbnail.jpg"]:
            self.write(path)
        site_output.filter_hidden_output_files(str(self.root), "")
        self.assertEqual({"index.html", "assets/_thumbnail.jpg"}, self.files())

    def test_exact_files_and_directory_subtrees_preserve_root_layout(self):
        for path in [".htaccess", ".env", ".well-known/acme/token", ".well-known/other",
                     "nested/.hidden/file", "nested/.hidden/.nested"]:
            self.write(path)
        site_output.filter_hidden_output_files(
            str(self.root), ".htaccess\n.well-known/acme/token\nnested/.hidden/\n")
        self.assertEqual({"index.html", ".htaccess", ".well-known/acme/token",
                          "nested/.hidden/file", "nested/.hidden/.nested"}, self.files())

    def test_invalid_or_missing_entries_fail_before_removing_files(self):
        self.write(".env")
        for entry in ["../.env", "/.env", ".hidden/../.env", ".hidden\\secret", ".missing",
                      "index.html", ".hidden/*", "C:/.env"]:
            with self.subTest(entry=entry), self.assertRaises(ValueError):
                site_output.filter_hidden_output_files(str(self.root), entry)
            self.assertTrue((self.root / ".env").exists())

    def test_in_place_and_source_directory_filtering_are_rejected(self):
        for output in ["", ".", "..", "your_content", "your_content/site_root", "comic_git_engine"]:
            with self.subTest(output=output), self.assertRaisesRegex(ValueError, "separate output"):
                site_output.validate_hidden_path_policy(output, "")

    def test_site_root_copy_is_filtered_without_changing_source(self):
        source = Path(self.temp.name) / "site_root"
        source.mkdir()
        (source / ".htaccess").write_text("rules")
        (source / ".env").write_text("private")
        with patch.object(site_output, "SITE_ROOT_SOURCE", str(source)):
            site_output.copy_site_root_files(str(self.root))
        site_output.filter_hidden_output_files(str(self.root), ".htaccess")
        self.assertEqual({"index.html", ".htaccess"}, self.files())
        self.assertEqual("private", (source / ".env").read_text())

    def test_symlinks_are_rejected_without_touching_external_files(self):
        external = Path(self.temp.name) / ".external"
        external.write_text("keep")
        try:
            (self.root / "linked").symlink_to(external)
        except OSError:
            self.skipTest("Creating symlinks is unavailable on this host")
        with self.assertRaisesRegex(ValueError, "symlinks"):
            site_output.filter_hidden_output_files(str(self.root), "")
        self.assertEqual("keep", external.read_text())


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

    def test_delete_output_file_space_loads_toml_for_legacy_in_place_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = os.getcwd()
            os.makedirs(os.path.join(temp_dir, "your_content"))
            os.makedirs(os.path.join(temp_dir, "comic"))
            os.makedirs(os.path.join(temp_dir, "about"))
            os.makedirs(os.path.join(temp_dir, "extras", "story"))
            with open(
                    os.path.join(temp_dir, "your_content", "comic_info.toml"),
                    "w",
                    encoding="utf-8",
            ) as f:
                f.write(
                    '[site]\nextra_comics = ["extras/story"]\n\n'
                    '[[pages]]\ntemplate_name = "about"\ntitle = "About"\n'
                )
            try:
                os.chdir(temp_dir)
                with patch.dict(os.environ, {"OUTPUT_DIR": ""}, clear=False):
                    site_output.delete_output_file_space()
            finally:
                os.chdir(cwd)

            self.assertFalse(os.path.exists(os.path.join(temp_dir, "comic")))
            self.assertFalse(os.path.exists(os.path.join(temp_dir, "about")))
            self.assertFalse(os.path.exists(os.path.join(temp_dir, "extras", "story")))

    def test_remove_generated_cms_files_removes_only_marked_files_and_empty_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            admin_dir = os.path.join(temp_dir, "admin")
            os.makedirs(admin_dir)
            for filename in ("index.html", "config.yml"):
                with open(os.path.join(admin_dir, filename), "w", encoding="utf-8") as f:
                    f.write(f"# {site_output.GENERATED_FILE_MARKER}\n")

            site_output.remove_generated_cms_files(temp_dir)

            self.assertFalse(os.path.exists(admin_dir))

    def test_remove_generated_cms_files_preserves_user_files_and_admin_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            admin_dir = os.path.join(temp_dir, "admin")
            os.makedirs(admin_dir)
            index_path = os.path.join(admin_dir, "index.html")
            config_path = os.path.join(admin_dir, "config.yml")
            asset_path = os.path.join(admin_dir, "custom.css")
            with open(index_path, "w", encoding="utf-8") as f:
                f.write("user index")
            with open(config_path, "w", encoding="utf-8") as f:
                f.write("user config")
            with open(asset_path, "w", encoding="utf-8") as f:
                f.write("user asset")

            site_output.remove_generated_cms_files(temp_dir)

            self.assertTrue(os.path.isfile(index_path))
            self.assertTrue(os.path.isfile(config_path))
            self.assertTrue(os.path.isfile(asset_path))
            self.assertTrue(os.path.isdir(admin_dir))

    def test_remove_generated_cms_files_preserves_non_utf8_user_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            admin_dir = os.path.join(temp_dir, "admin")
            os.makedirs(admin_dir)
            index_path = os.path.join(admin_dir, "index.html")
            with open(index_path, "wb") as f:
                f.write(b"\xff\xfe user content")

            site_output.remove_generated_cms_files(temp_dir)

            self.assertTrue(os.path.isfile(index_path))
            self.assertTrue(os.path.isdir(admin_dir))

    @patch(MUT + "delete_output_file_space")
    def test_setup_output_file_space_delegates_to_delete(self, mock_delete_output_file_space):
        comic_info = self.make_comic_info()

        site_output.setup_output_file_space(comic_info)

        mock_delete_output_file_space.assert_called_once_with(comic_info)

    @patch(MUT + "shutil.copytree")
    def test_copy_output_assets_only_runs_when_output_dir_is_set(self, mock_copytree):
        site_output.copy_output_assets("")
        mock_copytree.assert_not_called()

        site_output.copy_output_assets("output")

        self.assertEqual(4, mock_copytree.call_count)
        self.assertIn(
            (
                "comic_git_engine/schemas",
                os.path.join("output", "comic_git_engine/schemas"),
            ),
            [call.args for call in mock_copytree.call_args_list],
        )

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

    def test_copy_site_root_files_warns_when_overwriting_existing_file(self):
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
                with self.assertLogs("build.output.site_output", level="WARNING") as logs:
                    site_output.copy_site_root_files(output_dir)
            finally:
                os.chdir(cwd)

            self.assertIn(
                f"Overwriting existing output file with site_root file: {os.path.join(output_dir, 'favicon.ico')}",
                "\n".join(logs.output),
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
