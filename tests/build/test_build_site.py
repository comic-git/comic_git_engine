import os
from configparser import RawConfigParser
from unittest import TestCase
from unittest.mock import call, patch

import core.models as models
from build import build_site


COMIC_URL = "https://ryanvilbrandt.github.io/comic_git_dev"
MUT = "build.build_site."


def get_mock_dict(mocks):
    return {mock._mock_name: mock for mock in mocks}


@patch(MUT + "print_processing_times")
@patch(MUT + "checkpoint")
@patch(MUT + "copy_site_root_files")
@patch(MUT + "copy_output_assets")
@patch(MUT + "build_rss_feed_from_job")
@patch(MUT + "get_rss_feed_jobs", return_value=[])
@patch(MUT + "build_and_publish_comic_pages", return_value=([{"page_name": "Page 1"}], {"theme": "default"}))
@patch(MUT + "get_extra_comics_list", return_value=[])
@patch(MUT + "setup_output_file_space")
@patch(MUT + "run_hook", return_value=None)
@patch(MUT + "utils.get_comic_url", return_value=(COMIC_URL, "/comic_git_dev"))
@patch(MUT + "read_info")
@patch(MUT + "utils.find_project_root")
@patch(MUT + "add_inputs_to_env_vars")
class TestMain(TestCase):

    def make_comic_info(self):
        comic_info = RawConfigParser()
        comic_info.add_section("Comic Settings")
        comic_info.set("Comic Settings", "Theme", "default")
        comic_info.add_section("RSS Feed")
        comic_info.set("RSS Feed", "Build RSS feed", "True")
        return comic_info

    def test_main_builds_rss_feed_job_from_main_comic(self, *_mocks):
        m = get_mock_dict(_mocks)
        comic_info = self.make_comic_info()
        m["read_info"].return_value = comic_info
        comic_data_dicts = [{"page_name": "Page 1"}]
        global_values = {"theme": "default"}
        m["build_and_publish_comic_pages"].return_value = (comic_data_dicts, global_values)
        feed_job = object()
        m["get_rss_feed_jobs"].return_value = [feed_job]

        build_site.main()

        m["get_rss_feed_jobs"].assert_called_once_with(
            [models.ComicBuildResult("", comic_info, comic_data_dicts, global_values)]
        )
        m["build_rss_feed_from_job"].assert_called_once_with(feed_job)
        m["copy_output_assets"].assert_called_once_with("build")
        m["copy_site_root_files"].assert_called_once_with("build")

    @patch(MUT + "os.makedirs")
    @patch(MUT + "get_extra_comic_info")
    def test_main_builds_extra_comics_before_main_comic(self, *_mocks):
        m = get_mock_dict(_mocks)
        comic_info = self.make_comic_info()
        extra_comic_info = self.make_comic_info()
        m["read_info"].return_value = comic_info
        m["get_extra_comic_info"].return_value = extra_comic_info
        m["get_extra_comics_list"].return_value = ["extras/story"]
        m["build_and_publish_comic_pages"].side_effect = [
            ([{"page_name": "Extra 1"}], {"theme": "default"}),
            ([{"page_name": "Main 1"}], {"theme": "default"}),
        ]

        build_site.main()

        self.assertEqual(
            [
                call(COMIC_URL, "extras/story/", extra_comic_info, False, False),
                call(COMIC_URL, "", comic_info, False, False, {"extras/story": {"page_name": "Extra 1"}}),
            ],
            m["build_and_publish_comic_pages"].call_args_list,
        )
        m["makedirs"].assert_called_once_with(os.path.join("build", "extras/story"), exist_ok=True)
        m["copy_site_root_files"].assert_called_once_with("build")

    def test_main_copies_output_assets_when_output_dir_defaults_to_build(self, *_mocks):
        m = get_mock_dict(_mocks)
        m["read_info"].return_value = self.make_comic_info()

        build_site.main()

        m["copy_output_assets"].assert_called_once_with("build")
        m["copy_site_root_files"].assert_called_once_with("build")

    def test_main_copies_output_assets_when_output_dir_is_set(self, *_mocks):
        m = get_mock_dict(_mocks)
        m["read_info"].return_value = self.make_comic_info()

        with patch.dict("os.environ", {"OUTPUT_DIR": "output"}, clear=False):
            build_site.main()

        m["copy_output_assets"].assert_called_once_with("output")
        m["copy_site_root_files"].assert_called_once_with("output")

    def test_main_skips_copying_output_assets_when_output_dir_is_explicitly_blank(self, *_mocks):
        m = get_mock_dict(_mocks)
        m["read_info"].return_value = self.make_comic_info()

        with patch.dict("os.environ", {"OUTPUT_DIR": ""}, clear=False):
            build_site.main()

        m["copy_output_assets"].assert_not_called()
        m["copy_site_root_files"].assert_called_once_with("")

    def test_main_records_checkpoint_after_copying_site_root_files(self, *_mocks):
        m = get_mock_dict(_mocks)
        m["read_info"].return_value = self.make_comic_info()

        build_site.main()

        m["copy_site_root_files"].assert_called_once_with("build")
        self.assertIn(call("Copy site_root files"), m["checkpoint"].call_args_list)

    def test_main_surfaces_missing_site_root_folder(self, *_mocks):
        m = get_mock_dict(_mocks)
        m["read_info"].return_value = self.make_comic_info()
        m["copy_site_root_files"].side_effect = FileNotFoundError("your_content/site_root")

        with self.assertRaisesRegex(FileNotFoundError, "your_content/site_root"):
            build_site.main()

    def test_main_surfaces_build_failures(self, *_mocks):
        m = get_mock_dict(_mocks)
        m["read_info"].return_value = self.make_comic_info()
        m["build_and_publish_comic_pages"].side_effect = RuntimeError("build failed")

        with self.assertRaisesRegex(RuntimeError, "build failed"):
            build_site.main()


class TestCliArgs(TestCase):

    def test_parse_args_reads_output_dir(self):
        args = build_site.parse_args(["--output-dir", "preview_site"])

        self.assertEqual("preview_site", args.output_dir)
        self.assertFalse(args.delete_scheduled_posts)
        self.assertFalse(args.publish_all_comics)

    def test_apply_cli_environment_overrides_sets_output_dir(self):
        args = build_site.parse_args(["--output-dir", "preview_site"])

        with patch.dict("os.environ", {}, clear=False):
            build_site.apply_cli_environment_overrides(args)

            self.assertEqual("preview_site", os.environ["OUTPUT_DIR"])

    def test_apply_cli_environment_overrides_leaves_existing_output_dir_when_arg_missing(self):
        args = build_site.parse_args([])

        with patch.dict("os.environ", {"OUTPUT_DIR": "env_output"}, clear=False):
            build_site.apply_cli_environment_overrides(args)

            self.assertEqual("env_output", os.environ["OUTPUT_DIR"])
