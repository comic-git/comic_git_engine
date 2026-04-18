import os
from configparser import RawConfigParser
from unittest import TestCase
from unittest.mock import call, patch

import core.models as models
from build import build_site


COMIC_URL = "https://ryanvilbrandt.github.io/comic_git_dev"


class TestMain(TestCase):

    def make_comic_info(self):
        comic_info = RawConfigParser()
        comic_info.add_section("Comic Settings")
        comic_info.set("Comic Settings", "Theme", "default")
        comic_info.add_section("RSS Feed")
        comic_info.set("RSS Feed", "Build RSS feed", "True")
        return comic_info

    @patch("build.build_site.print_processing_times")
    @patch("build.build_site.checkpoint")
    @patch("build.build_site.copy_site_root_files")
    @patch("build.build_site.copy_output_assets")
    @patch("build.build_site.build_rss_feed_from_job")
    @patch("build.build_site.get_rss_feed_jobs")
    @patch("build.build_site.build_and_publish_comic_pages")
    @patch("build.build_site.get_extra_comics_list", return_value=[])
    @patch("build.build_site.setup_output_file_space")
    @patch("build.build_site.run_hook")
    @patch("build.build_site.utils.get_comic_url", return_value=(COMIC_URL, "/comic_git_dev"))
    @patch("build.build_site.read_info")
    @patch("build.build_site.utils.find_project_root")
    @patch("build.build_site.add_inputs_to_env_vars")
    def test_main_builds_rss_feed_job_from_main_comic(
            self,
            _mock_add_inputs_to_env_vars,
            _mock_find_project_root,
            mock_read_info,
            _mock_get_comic_url,
            mock_run_hook,
            _mock_setup_output_file_space,
            _mock_get_extra_comics_list,
            mock_build_and_publish_comic_pages,
            mock_get_rss_feed_jobs,
            mock_build_rss_feed_from_job,
            mock_copy_output_assets,
            mock_copy_site_root_files,
            _mock_checkpoint,
            _mock_print_processing_times,
    ):
        comic_info = self.make_comic_info()
        mock_read_info.return_value = comic_info
        mock_run_hook.return_value = None
        comic_data_dicts = [{"page_name": "Page 1"}]
        global_values = {"theme": "default"}
        mock_build_and_publish_comic_pages.return_value = (comic_data_dicts, global_values)
        feed_job = object()
        mock_get_rss_feed_jobs.return_value = [feed_job]

        build_site.main()

        mock_get_rss_feed_jobs.assert_called_once_with(
            [models.ComicBuildResult("", comic_info, comic_data_dicts, global_values)]
        )
        mock_build_rss_feed_from_job.assert_called_once_with(feed_job)
        mock_copy_output_assets.assert_called_once_with("build")
        mock_copy_site_root_files.assert_called_once_with("build")

    @patch("build.build_site.print_processing_times")
    @patch("build.build_site.checkpoint")
    @patch("build.build_site.copy_site_root_files")
    @patch("build.build_site.copy_output_assets")
    @patch("build.build_site.build_rss_feed_from_job")
    @patch("build.build_site.get_rss_feed_jobs", return_value=[])
    @patch("build.build_site.build_and_publish_comic_pages")
    @patch("build.build_site.get_extra_comic_info")
    @patch("build.build_site.get_extra_comics_list", return_value=["extras/story"])
    @patch("build.build_site.setup_output_file_space")
    @patch("build.build_site.os.makedirs")
    @patch("build.build_site.run_hook")
    @patch("build.build_site.utils.get_comic_url", return_value=(COMIC_URL, "/comic_git_dev"))
    @patch("build.build_site.read_info")
    @patch("build.build_site.utils.find_project_root")
    @patch("build.build_site.add_inputs_to_env_vars")
    def test_main_builds_extra_comics_before_main_comic(
            self,
            _mock_add_inputs_to_env_vars,
            _mock_find_project_root,
            mock_read_info,
            _mock_get_comic_url,
            mock_run_hook,
            mock_os_makedirs,
            _mock_setup_output_file_space,
            _mock_get_extra_comics_list,
            mock_get_extra_comic_info,
            mock_build_and_publish_comic_pages,
            _mock_get_rss_feed_jobs,
            _mock_build_rss_feed_from_job,
            _mock_copy_output_assets,
            mock_copy_site_root_files,
            _mock_checkpoint,
            _mock_print_processing_times,
    ):
        comic_info = self.make_comic_info()
        extra_comic_info = self.make_comic_info()
        mock_read_info.return_value = comic_info
        mock_get_extra_comic_info.return_value = extra_comic_info
        mock_run_hook.return_value = None
        mock_build_and_publish_comic_pages.side_effect = [
            ([{"page_name": "Extra 1"}], {"theme": "default"}),
            ([{"page_name": "Main 1"}], {"theme": "default"}),
        ]

        build_site.main()

        self.assertEqual(
            [
                call(COMIC_URL, "extras/story/", extra_comic_info, False, False),
                call(COMIC_URL, "", comic_info, False, False, {"extras/story": {"page_name": "Extra 1"}}),
            ],
            mock_build_and_publish_comic_pages.call_args_list,
        )
        mock_os_makedirs.assert_called_once_with(os.path.join("build", "extras/story"), exist_ok=True)
        mock_copy_site_root_files.assert_called_once_with("build")

    @patch("build.build_site.print_processing_times")
    @patch("build.build_site.checkpoint")
    @patch("build.build_site.copy_site_root_files")
    @patch("build.build_site.copy_output_assets")
    @patch("build.build_site.build_rss_feed_from_job")
    @patch("build.build_site.get_rss_feed_jobs", return_value=[])
    @patch("build.build_site.build_and_publish_comic_pages", return_value=([{"page_name": "Page 1"}], {"theme": "default"}))
    @patch("build.build_site.get_extra_comics_list", return_value=[])
    @patch("build.build_site.setup_output_file_space")
    @patch("build.build_site.run_hook")
    @patch("build.build_site.utils.get_comic_url", return_value=(COMIC_URL, "/comic_git_dev"))
    @patch("build.build_site.read_info")
    @patch("build.build_site.utils.find_project_root")
    @patch("build.build_site.add_inputs_to_env_vars")
    def test_main_copies_output_assets_when_output_dir_defaults_to_build(
            self,
            _mock_add_inputs_to_env_vars,
            _mock_find_project_root,
            mock_read_info,
            _mock_get_comic_url,
            mock_run_hook,
            _mock_setup_output_file_space,
            _mock_get_extra_comics_list,
            _mock_build_and_publish_comic_pages,
            _mock_get_rss_feed_jobs,
            _mock_build_rss_feed_from_job,
            mock_copy_output_assets,
            mock_copy_site_root_files,
            _mock_checkpoint,
            _mock_print_processing_times,
    ):
        mock_read_info.return_value = self.make_comic_info()
        mock_run_hook.return_value = None

        build_site.main()

        mock_copy_output_assets.assert_called_once_with("build")
        mock_copy_site_root_files.assert_called_once_with("build")

    @patch("build.build_site.print_processing_times")
    @patch("build.build_site.checkpoint")
    @patch("build.build_site.copy_site_root_files")
    @patch("build.build_site.copy_output_assets")
    @patch("build.build_site.build_rss_feed_from_job")
    @patch("build.build_site.get_rss_feed_jobs", return_value=[])
    @patch("build.build_site.build_and_publish_comic_pages", return_value=([{"page_name": "Page 1"}], {"theme": "default"}))
    @patch("build.build_site.get_extra_comics_list", return_value=[])
    @patch("build.build_site.setup_output_file_space")
    @patch("build.build_site.run_hook")
    @patch("build.build_site.utils.get_comic_url", return_value=(COMIC_URL, "/comic_git_dev"))
    @patch("build.build_site.read_info")
    @patch("build.build_site.utils.find_project_root")
    @patch("build.build_site.add_inputs_to_env_vars")
    def test_main_copies_output_assets_when_output_dir_is_set(
            self,
            _mock_add_inputs_to_env_vars,
            _mock_find_project_root,
            mock_read_info,
            _mock_get_comic_url,
            mock_run_hook,
            _mock_setup_output_file_space,
            _mock_get_extra_comics_list,
            _mock_build_and_publish_comic_pages,
            _mock_get_rss_feed_jobs,
            _mock_build_rss_feed_from_job,
            mock_copy_output_assets,
            mock_copy_site_root_files,
            _mock_checkpoint,
            _mock_print_processing_times,
    ):
        mock_read_info.return_value = self.make_comic_info()
        mock_run_hook.return_value = None

        with patch.dict("os.environ", {"OUTPUT_DIR": "output"}, clear=False):
            build_site.main()

        mock_copy_output_assets.assert_called_once_with("output")
        mock_copy_site_root_files.assert_called_once_with("output")

    @patch("build.build_site.print_processing_times")
    @patch("build.build_site.checkpoint")
    @patch("build.build_site.copy_site_root_files")
    @patch("build.build_site.copy_output_assets")
    @patch("build.build_site.build_rss_feed_from_job")
    @patch("build.build_site.get_rss_feed_jobs", return_value=[])
    @patch("build.build_site.build_and_publish_comic_pages", return_value=([{"page_name": "Page 1"}], {"theme": "default"}))
    @patch("build.build_site.get_extra_comics_list", return_value=[])
    @patch("build.build_site.setup_output_file_space")
    @patch("build.build_site.run_hook")
    @patch("build.build_site.utils.get_comic_url", return_value=(COMIC_URL, "/comic_git_dev"))
    @patch("build.build_site.read_info")
    @patch("build.build_site.utils.find_project_root")
    @patch("build.build_site.add_inputs_to_env_vars")
    def test_main_skips_copying_output_assets_when_output_dir_is_explicitly_blank(
            self,
            _mock_add_inputs_to_env_vars,
            _mock_find_project_root,
            mock_read_info,
            _mock_get_comic_url,
            mock_run_hook,
            _mock_setup_output_file_space,
            _mock_get_extra_comics_list,
            _mock_build_and_publish_comic_pages,
            _mock_get_rss_feed_jobs,
            _mock_build_rss_feed_from_job,
            mock_copy_output_assets,
            mock_copy_site_root_files,
            _mock_checkpoint,
            _mock_print_processing_times,
    ):
        mock_read_info.return_value = self.make_comic_info()
        mock_run_hook.return_value = None

        with patch.dict("os.environ", {"OUTPUT_DIR": ""}, clear=False):
            build_site.main()

        mock_copy_output_assets.assert_not_called()
        mock_copy_site_root_files.assert_called_once_with("")

    @patch("build.build_site.print_processing_times")
    @patch("build.build_site.checkpoint")
    @patch("build.build_site.copy_site_root_files")
    @patch("build.build_site.copy_output_assets")
    @patch("build.build_site.build_rss_feed_from_job")
    @patch("build.build_site.get_rss_feed_jobs", return_value=[])
    @patch("build.build_site.build_and_publish_comic_pages", return_value=([{"page_name": "Page 1"}], {"theme": "default"}))
    @patch("build.build_site.get_extra_comics_list", return_value=[])
    @patch("build.build_site.setup_output_file_space")
    @patch("build.build_site.run_hook")
    @patch("build.build_site.utils.get_comic_url", return_value=(COMIC_URL, "/comic_git_dev"))
    @patch("build.build_site.read_info")
    @patch("build.build_site.utils.find_project_root")
    @patch("build.build_site.add_inputs_to_env_vars")
    def test_main_records_checkpoint_after_copying_site_root_files(
            self,
            _mock_add_inputs_to_env_vars,
            _mock_find_project_root,
            mock_read_info,
            _mock_get_comic_url,
            mock_run_hook,
            _mock_setup_output_file_space,
            _mock_get_extra_comics_list,
            _mock_build_and_publish_comic_pages,
            _mock_get_rss_feed_jobs,
            _mock_build_rss_feed_from_job,
            _mock_copy_output_assets,
            mock_copy_site_root_files,
            mock_checkpoint,
            _mock_print_processing_times,
    ):
        mock_read_info.return_value = self.make_comic_info()
        mock_run_hook.return_value = None

        build_site.main()

        mock_copy_site_root_files.assert_called_once_with("build")
        self.assertIn(call("Copy site_root files"), mock_checkpoint.call_args_list)

    @patch("build.build_site.print_processing_times")
    @patch("build.build_site.checkpoint")
    @patch("build.build_site.copy_site_root_files", side_effect=FileNotFoundError("your_content/site_root"))
    @patch("build.build_site.copy_output_assets")
    @patch("build.build_site.build_rss_feed_from_job")
    @patch("build.build_site.get_rss_feed_jobs", return_value=[])
    @patch("build.build_site.build_and_publish_comic_pages", return_value=([{"page_name": "Page 1"}], {"theme": "default"}))
    @patch("build.build_site.get_extra_comics_list", return_value=[])
    @patch("build.build_site.setup_output_file_space")
    @patch("build.build_site.run_hook")
    @patch("build.build_site.utils.get_comic_url", return_value=(COMIC_URL, "/comic_git_dev"))
    @patch("build.build_site.read_info")
    @patch("build.build_site.utils.find_project_root")
    @patch("build.build_site.add_inputs_to_env_vars")
    def test_main_surfaces_missing_site_root_folder(
            self,
            _mock_add_inputs_to_env_vars,
            _mock_find_project_root,
            mock_read_info,
            _mock_get_comic_url,
            mock_run_hook,
            _mock_setup_output_file_space,
            _mock_get_extra_comics_list,
            _mock_build_and_publish_comic_pages,
            _mock_get_rss_feed_jobs,
            _mock_build_rss_feed_from_job,
            _mock_copy_output_assets,
            _mock_copy_site_root_files,
            _mock_checkpoint,
            _mock_print_processing_times,
    ):
        mock_read_info.return_value = self.make_comic_info()
        mock_run_hook.return_value = None

        with self.assertRaisesRegex(FileNotFoundError, "your_content/site_root"):
            build_site.main()

    @patch("build.build_site.print_processing_times")
    @patch("build.build_site.checkpoint")
    @patch("build.build_site.copy_site_root_files")
    @patch("build.build_site.copy_output_assets")
    @patch("build.build_site.build_rss_feed_from_job")
    @patch("build.build_site.get_rss_feed_jobs", return_value=[])
    @patch("build.build_site.build_and_publish_comic_pages", side_effect=RuntimeError("build failed"))
    @patch("build.build_site.get_extra_comics_list", return_value=[])
    @patch("build.build_site.setup_output_file_space")
    @patch("build.build_site.run_hook")
    @patch("build.build_site.utils.get_comic_url", return_value=(COMIC_URL, "/comic_git_dev"))
    @patch("build.build_site.read_info")
    @patch("build.build_site.utils.find_project_root")
    @patch("build.build_site.add_inputs_to_env_vars")
    def test_main_surfaces_build_failures(
            self,
            _mock_add_inputs_to_env_vars,
            _mock_find_project_root,
            mock_read_info,
            _mock_get_comic_url,
            mock_run_hook,
            _mock_setup_output_file_space,
            _mock_get_extra_comics_list,
            _mock_build_and_publish_comic_pages,
            _mock_get_rss_feed_jobs,
            _mock_build_rss_feed_from_job,
            _mock_copy_output_assets,
            _mock_copy_site_root_files,
            _mock_checkpoint,
            _mock_print_processing_times,
    ):
        mock_read_info.return_value = self.make_comic_info()
        mock_run_hook.return_value = None

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
