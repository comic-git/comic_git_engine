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
        mock_copy_output_assets.assert_not_called()

    @patch("build.build_site.print_processing_times")
    @patch("build.build_site.checkpoint")
    @patch("build.build_site.copy_output_assets")
    @patch("build.build_site.build_rss_feed_from_job")
    @patch("build.build_site.get_rss_feed_jobs", return_value=[])
    @patch("build.build_site.build_and_publish_comic_pages")
    @patch("build.build_site.get_extra_comic_info")
    @patch("build.build_site.get_extra_comics_list", return_value=["extras/story"])
    @patch("build.build_site.setup_output_file_space")
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
            _mock_setup_output_file_space,
            _mock_get_extra_comics_list,
            mock_get_extra_comic_info,
            mock_build_and_publish_comic_pages,
            _mock_get_rss_feed_jobs,
            _mock_build_rss_feed_from_job,
            _mock_copy_output_assets,
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

    @patch("build.build_site.print_processing_times")
    @patch("build.build_site.checkpoint")
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
            _mock_checkpoint,
            _mock_print_processing_times,
    ):
        mock_read_info.return_value = self.make_comic_info()
        mock_run_hook.return_value = None

        with patch.dict("os.environ", {"OUTPUT_DIR": "output"}, clear=False):
            build_site.main()

        mock_copy_output_assets.assert_called_once_with("output")

    @patch("build.build_site.print_processing_times")
    @patch("build.build_site.checkpoint")
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
            _mock_checkpoint,
            _mock_print_processing_times,
    ):
        mock_read_info.return_value = self.make_comic_info()
        mock_run_hook.return_value = None

        with self.assertRaisesRegex(RuntimeError, "build failed"):
            build_site.main()
