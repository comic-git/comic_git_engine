from configparser import RawConfigParser
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch, MagicMock

import build_rss_feed
import models
import utils
from build_site import resize
from scripts import build_site

MUT = "scripts.build_site."

COMIC_URL = "https://ryanvilbrandt.github.io/comic_git_dev"
WEBRING_JSON = {
    "version": 1,
    "name": "Our Comics Webring!",
    "home": {
        "name": "Home",
        "url": "https://my.webring.com/",
        "image": "https://my.webring.com/icon.png"
    },
    "members": [
        {
            "id": "comic_a",
            "name": "Albert's Atrium",
            "url": "https://comic.albert.net/",
            "image": "https://comic.albert.net/icon.png"
        },
        {
            "id": "comic_b",
            "name": "Bertrand's Barn",
            "url": "https://bertrand.github.io/my_barn",
            "image": "https://bertrand.github.io/my_barn/your_content/images/webring.jpg"
        },
        {
            "id": "comic_c",
            "name": "Clara's Cliffside",
            "url": "https://clara-is-cool.neocities.org/",
            "image": "https://images.ctfassets.net/hrltx12pl8hq/7JnR6tVVwDyUM8Cbci3GtJ/bf74366cff2ba271471725d0b0ef418c/shutterstock_376532611-og.jpg"
        }
    ]
}


class TestImageUtils(TestCase):

    def test_resize_set_size(self):
        im = MagicMock()
        im.size = 100, 200
        self.assertEqual(im.resize.return_value, resize(im, " 150, 350 "))
        im.resize.assert_called_once_with((150, 350))

    def test_resize_percentage(self):
        im = MagicMock()
        im.size = 100, 200
        self.assertEqual(im.resize.return_value, resize(im, "50%"))
        im.resize.assert_called_once_with((50, 100))

    def test_resize_set_height(self):
        im = MagicMock()
        im.size = 100, 200
        self.assertEqual(im.resize.return_value, resize(im, "220h"))
        im.resize.assert_called_once_with((110, 220))

    def test_resize_set_width(self):
        im = MagicMock()
        im.size = 100, 200
        self.assertEqual(im.resize.return_value, resize(im, "110w"))
        im.resize.assert_called_once_with((110, 220))

    def test_resize_exception(self):
        im = MagicMock()
        im.size = 100, 200
        with self.assertRaisesRegex(ValueError, "Unknown resize value:"):
            resize(im, "farts lol")
        im.resize.assert_not_called()


@patch(MUT + "json.load", return_value=WEBRING_JSON)
@patch(MUT + "urlopen")
class TestLoadWebringData(TestCase):
    def setUp(self):
        # Create a mock RawConfigParser
        self.comic_info = RawConfigParser()
        self.comic_info.add_section("Webring")
        self.comic_info.set("Webring", "Enable webring", "True")
        self.comic_info.set("Webring", "Endpoint", "https://webring.example.com/api")
        self.comic_info.set("Webring", "Webring ID", "comic_b")

    def test_enable_webring_false(self, _mock_urlopen, _mock_json_load):
        """If Enable webring is False, should return {"enable_webring": False}"""
        self.comic_info.set("Webring", "Enable webring", "False")
        self.assertEqual(
            {"enable_webring": False},
            build_site.load_webring_data(self.comic_info, COMIC_URL),
        )
        _mock_urlopen.assert_not_called()

    def test_undefined_endpoint(self, _mock_urlopen, _mock_json_load):
        """If Endpoint is not defined, should raise ValueError"""
        self.comic_info.set("Webring", "Endpoint", "")
        msg = r"The 'Endpoint' option in the \[Webring\] section must be defined when 'Enable webring' is enabled."
        with self.assertRaisesRegex(ValueError, msg):
            build_site.load_webring_data(self.comic_info, COMIC_URL)
        _mock_urlopen.assert_not_called()

    def test_invalid_version(self, _mock_urlopen, _mock_json_load):
        """Raises ValueError on an invalid version"""
        webring_json = deepcopy(WEBRING_JSON)
        webring_json["version"] = 10
        _mock_json_load.return_value = webring_json
        with self.assertRaisesRegex(ValueError, "Unknown webring data version: 10"):
            build_site.load_webring_data(self.comic_info, COMIC_URL)

    def test_invalid_webring_id(self, _mock_urlopen, _mock_json_load):
        """Raises ValueError when Webring ID isn't defined"""
        self.comic_info.set("Webring", "Webring ID", "")
        msg = r"The 'Webring ID' option in the \[Webring\] section must be defined when 'Enable webring' is enabled and 'Show all members' is False."
        with self.assertRaisesRegex(ValueError, msg):
            build_site.load_webring_data(self.comic_info, COMIC_URL)

    def test_webring_id_not_found(self, _mock_urlopen, _mock_json_load):
        """Raises ValueError when Webring ID isn't found in the list of members"""
        self.comic_info.set("Webring", "Webring ID", "not_a_real_id")
        msg = r"Couldn't find 'not_a_real_id' in the list of members. See the logs for the webring data that was received."
        with self.assertRaisesRegex(ValueError, msg):
            build_site.load_webring_data(self.comic_info, COMIC_URL)

    def test_assert_urlopen(self, _mock_urlopen, _mock_json_load):
        """Should call urlopen with the correct endpoint and return the JSON data"""
        self.assertEqual(
            {
                "enable_webring": True,
                "webring_name": "Our Comics Webring!",
                "webring_home": {
                    "name": "Home",
                    "url": "https://my.webring.com/",
                    "image": "https://my.webring.com/icon.png"
                },
                "show_all_members": False,
                "webring_prev": {
                    "id": "comic_a",
                    "name": "Albert's Atrium",
                    "url": "https://comic.albert.net/",
                    "image": "https://comic.albert.net/icon.png"
                },
                "webring_next": {
                    "id": "comic_c",
                    "name": "Clara's Cliffside",
                    "url": "https://clara-is-cool.neocities.org/",
                    "image": "https://images.ctfassets.net/hrltx12pl8hq/7JnR6tVVwDyUM8Cbci3GtJ/bf74366cff2ba271471725d0b0ef418c/shutterstock_376532611-og.jpg"
                }
            },
            build_site.load_webring_data(self.comic_info, COMIC_URL),
        )
        _mock_urlopen.assert_called_once_with("https://webring.example.com/api")

    def test_relative_path(self, _mock_urlopen, _mock_json_load):
        """"""
        self.comic_info.set("Webring", "Endpoint", "/your_content/webring.json")
        build_site.load_webring_data(self.comic_info, COMIC_URL)
        _mock_urlopen.assert_called_once_with("https://ryanvilbrandt.github.io/comic_git_dev/your_content/webring.json")

    def test_first_member(self, _mock_urlopen, _mock_json_load):
        """If we're the first member in the list, prev should wrap to the end"""
        self.comic_info.set("Webring", "Webring ID", "comic_a")
        self.assertEqual(
            {
                "enable_webring": True,
                "webring_name": "Our Comics Webring!",
                "webring_home": {
                    "name": "Home",
                    "url": "https://my.webring.com/",
                    "image": "https://my.webring.com/icon.png"
                },
                "show_all_members": False,
                "webring_prev": {
                    "id": "comic_c",
                    "name": "Clara's Cliffside",
                    "url": "https://clara-is-cool.neocities.org/",
                    "image": "https://images.ctfassets.net/hrltx12pl8hq/7JnR6tVVwDyUM8Cbci3GtJ/bf74366cff2ba271471725d0b0ef418c/shutterstock_376532611-og.jpg"
                },
                "webring_next": {
                    "id": "comic_b",
                    "name": "Bertrand's Barn",
                    "url": "https://bertrand.github.io/my_barn",
                    "image": "https://bertrand.github.io/my_barn/your_content/images/webring.jpg"
                }
            },
            build_site.load_webring_data(self.comic_info, COMIC_URL),
        )

    def test_last_member(self, _mock_urlopen, _mock_json_load):
        """If we're the last member in the list, next should wrap to the start"""
        self.comic_info.set("Webring", "Webring ID", "comic_c")
        self.assertEqual(
            {
                "enable_webring": True,
                "webring_name": "Our Comics Webring!",
                "webring_home": {
                    "name": "Home",
                    "url": "https://my.webring.com/",
                    "image": "https://my.webring.com/icon.png"
                },
                "show_all_members": False,
                "webring_prev": {
                    "id": "comic_b",
                    "name": "Bertrand's Barn",
                    "url": "https://bertrand.github.io/my_barn",
                    "image": "https://bertrand.github.io/my_barn/your_content/images/webring.jpg"
                },
                "webring_next": {
                    "id": "comic_a",
                    "name": "Albert's Atrium",
                    "url": "https://comic.albert.net/",
                    "image": "https://comic.albert.net/icon.png"
                }
            },
            build_site.load_webring_data(self.comic_info, COMIC_URL),
        )

    def test_show_all_members(self, _mock_urlopen, _mock_json_load):
        """If Show all members is True, should return all members and not prev/next"""
        self.comic_info.set("Webring", "Show all members", "True")
        self.assertEqual(
            {
                "enable_webring": True,
                "webring_name": "Our Comics Webring!",
                "webring_home": {
                    "name": "Home",
                    "url": "https://my.webring.com/",
                    "image": "https://my.webring.com/icon.png"
                },
                "show_all_members": True,
                "webring_members": [
                    {
                        "id": "comic_a",
                        "name": "Albert's Atrium",
                        "url": "https://comic.albert.net/",
                        "image": "https://comic.albert.net/icon.png"
                    },
                    {
                        "id": "comic_b",
                        "name": "Bertrand's Barn",
                        "url": "https://bertrand.github.io/my_barn",
                        "image": "https://bertrand.github.io/my_barn/your_content/images/webring.jpg"
                    },
                    {
                        "id": "comic_c",
                        "name": "Clara's Cliffside",
                        "url": "https://clara-is-cool.neocities.org/",
                        "image": "https://images.ctfassets.net/hrltx12pl8hq/7JnR6tVVwDyUM8Cbci3GtJ/bf74366cff2ba271471725d0b0ef418c/shutterstock_376532611-og.jpg"
                    }
                ]
            },
            build_site.load_webring_data(self.comic_info, COMIC_URL),
        )


@patch(MUT + "print_processing_times")
@patch(MUT + "checkpoint")
@patch(MUT + "build_rss_feed_from_job")
@patch(MUT + "get_rss_feed_jobs")
@patch(MUT + "build_and_publish_comic_pages")
@patch(MUT + "get_extra_comics_list", return_value=[])
@patch(MUT + "setup_output_file_space")
@patch(MUT + "run_hook")
@patch(MUT + "utils.get_comic_url", return_value=(COMIC_URL, "/comic_git_dev"))
@patch(MUT + "read_info")
@patch(MUT + "utils.find_project_root")
@patch(MUT + "add_inputs_to_env_vars")
class TestMain(TestCase):

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
            _mock_checkpoint,
            _mock_print_processing_times,
    ):
        comic_info = RawConfigParser()
        comic_info.add_section("Comic Settings")
        comic_info.set("Comic Settings", "Theme", "default")
        comic_info.add_section("RSS Feed")
        comic_info.set("RSS Feed", "Build RSS feed", "True")
        mock_read_info.return_value = comic_info
        mock_run_hook.return_value = None
        comic_data_dicts = [{"page_name": "Page 1"}]
        global_values = {"theme": "default"}
        mock_build_and_publish_comic_pages.return_value = (comic_data_dicts, global_values)
        feed_job = object()
        mock_get_rss_feed_jobs.return_value = [feed_job]

        build_site.main()

        mock_get_rss_feed_jobs.assert_called_once()
        self.assertEqual(
            (comic_info, [models.ComicBuildResult("", comic_info, comic_data_dicts, global_values)]),
            mock_get_rss_feed_jobs.call_args.args,
        )
        mock_build_rss_feed_from_job.assert_called_once_with(feed_job)


class TestRssFeedJobs(TestCase):

    def make_root_comic_info(
            self,
            rss_feed_mode: str | None = None,
            build_rss_feed: bool = True,
            rss_title_format: str = "",
    ):
        comic_info = RawConfigParser()
        comic_info.add_section("RSS Feed")
        comic_info.set("RSS Feed", "Build RSS feed", str(build_rss_feed))
        if rss_title_format:
            comic_info.set("RSS Feed", "RSS title format", rss_title_format)
        if rss_feed_mode is not None:
            comic_info.set("RSS Feed", "Feed mode", rss_feed_mode)
        return comic_info

    def make_comic_info(self, build_rss_feed: bool = True, comic_name: str = "Comic"):
        comic_info = RawConfigParser()
        comic_info.add_section("Comic Info")
        comic_info.set("Comic Info", "Comic name", comic_name)
        comic_info.add_section("RSS Feed")
        comic_info.set("RSS Feed", "Build RSS feed", str(build_rss_feed))
        return comic_info

    def test_build_rss_feed_job_for_main_comic(self):
        comic_info = self.make_comic_info()
        comic_result = models.ComicBuildResult(
            comic_folder="",
            comic_info=comic_info,
            comic_data_dicts=[{"page_name": "Page 1"}],
            global_values={},
        )

        feed_job = build_rss_feed.build_rss_feed_job_for_comic_result(comic_result)

        self.assertEqual(comic_info, feed_job.comic_info)
        self.assertEqual([{"page_name": "Page 1"}], feed_job.comic_data_dicts)
        self.assertEqual("feed.xml", feed_job.feed_relative_path)
        self.assertEqual("comic", feed_job.comic_page_relative_path)
        self.assertTrue(feed_job.build_enabled)

    def test_build_rss_feed_job_for_extra_comic_uses_folder_paths(self):
        comic_info = self.make_comic_info()
        comic_result = models.ComicBuildResult(
            comic_folder="extras/story/",
            comic_info=comic_info,
            comic_data_dicts=[{"page_name": "Page 1"}],
            global_values={},
        )

        feed_job = build_rss_feed.build_rss_feed_job_for_comic_result(comic_result)

        self.assertEqual("extras/story/feed.xml", feed_job.feed_relative_path)
        self.assertEqual("extras/story/comic", feed_job.comic_page_relative_path)

    def test_select_comic_results_for_rss_defaults_to_main_only(self):
        main_result = models.ComicBuildResult(
            comic_folder="",
            comic_info=self.make_comic_info(),
            comic_data_dicts=[{"page_name": "Main"}],
            global_values={},
        )
        extra_result = models.ComicBuildResult(
            comic_folder="extras/story/",
            comic_info=self.make_comic_info(),
            comic_data_dicts=[{"page_name": "Extra"}],
            global_values={},
        )

        selected_results = build_rss_feed.select_comic_results_for_rss(
            self.make_root_comic_info(),
            [extra_result, main_result],
        )

        self.assertEqual([main_result], selected_results)

    def test_select_comic_results_for_rss_main_only_skips_disabled_main(self):
        main_result = models.ComicBuildResult(
            comic_folder="",
            comic_info=self.make_comic_info(build_rss_feed=False),
            comic_data_dicts=[{"page_name": "Main"}],
            global_values={},
        )
        extra_result = models.ComicBuildResult(
            comic_folder="extras/story/",
            comic_info=self.make_comic_info(),
            comic_data_dicts=[{"page_name": "Extra"}],
            global_values={},
        )

        selected_results = build_rss_feed.select_comic_results_for_rss(
            self.make_root_comic_info(),
            [extra_result, main_result],
        )

        self.assertEqual([], selected_results)

    def test_select_comic_results_for_rss_supports_per_comic_mode(self):
        main_result = models.ComicBuildResult(
            comic_folder="",
            comic_info=self.make_comic_info(),
            comic_data_dicts=[{"page_name": "Main"}],
            global_values={},
        )
        extra_result = models.ComicBuildResult(
            comic_folder="extras/story/",
            comic_info=self.make_comic_info(),
            comic_data_dicts=[{"page_name": "Extra"}],
            global_values={},
        )

        selected_results = build_rss_feed.select_comic_results_for_rss(
            self.make_root_comic_info("per-comic"),
            [extra_result, main_result],
        )

        self.assertEqual([extra_result, main_result], selected_results)

    def test_select_comic_results_for_rss_per_comic_filters_disabled_comics(self):
        main_result = models.ComicBuildResult(
            comic_folder="",
            comic_info=self.make_comic_info(),
            comic_data_dicts=[{"page_name": "Main"}],
            global_values={},
        )
        extra_result = models.ComicBuildResult(
            comic_folder="extras/story/",
            comic_info=self.make_comic_info(build_rss_feed=False),
            comic_data_dicts=[{"page_name": "Extra"}],
            global_values={},
        )

        selected_results = build_rss_feed.select_comic_results_for_rss(
            self.make_root_comic_info("per-comic"),
            [extra_result, main_result],
        )

        self.assertEqual([main_result], selected_results)

    def test_select_comic_results_for_rss_supports_combined_mode(self):
        main_result = models.ComicBuildResult(
            comic_folder="",
            comic_info=self.make_comic_info(),
            comic_data_dicts=[{"page_name": "Main"}],
            global_values={},
        )
        extra_result = models.ComicBuildResult(
            comic_folder="extras/story/",
            comic_info=self.make_comic_info(),
            comic_data_dicts=[{"page_name": "Extra"}],
            global_values={},
        )

        selected_results = build_rss_feed.select_comic_results_for_rss(
            self.make_root_comic_info("combined"),
            [extra_result, main_result],
        )

        self.assertEqual([extra_result, main_result], selected_results)

    def test_select_comic_results_for_rss_combined_filters_disabled_comics(self):
        main_result = models.ComicBuildResult(
            comic_folder="",
            comic_info=self.make_comic_info(build_rss_feed=False),
            comic_data_dicts=[{"page_name": "Main"}],
            global_values={},
        )
        extra_result = models.ComicBuildResult(
            comic_folder="extras/story/",
            comic_info=self.make_comic_info(),
            comic_data_dicts=[{"page_name": "Extra"}],
            global_values={},
        )

        selected_results = build_rss_feed.select_comic_results_for_rss(
            self.make_root_comic_info("combined", build_rss_feed=False),
            [extra_result, main_result],
        )

        self.assertEqual([extra_result], selected_results)

    def test_select_comic_results_for_rss_rejects_unknown_mode(self):
        main_result = models.ComicBuildResult(
            comic_folder="",
            comic_info=self.make_comic_info(),
            comic_data_dicts=[{"page_name": "Main"}],
            global_values={},
        )

        with self.assertRaisesRegex(ValueError, "Unknown RSS feed mode: weird-mode"):
            build_rss_feed.select_comic_results_for_rss(
                self.make_root_comic_info("weird-mode"),
                [main_result],
            )

    def test_get_rss_feed_jobs_returns_jobs_for_selected_results(self):
        root_comic_info = self.make_root_comic_info("per-comic")
        main_result = models.ComicBuildResult(
            comic_folder="",
            comic_info=self.make_comic_info(),
            comic_data_dicts=[{"page_name": "Main"}],
            global_values={},
        )
        extra_result = models.ComicBuildResult(
            comic_folder="extras/story/",
            comic_info=self.make_comic_info(),
            comic_data_dicts=[{"page_name": "Extra"}],
            global_values={},
        )

        feed_jobs = build_rss_feed.get_rss_feed_jobs(root_comic_info, [extra_result, main_result])

        self.assertEqual(2, len(feed_jobs))
        self.assertEqual("extras/story/feed.xml", feed_jobs[0].feed_relative_path)
        self.assertEqual("extras/story/comic", feed_jobs[0].comic_page_relative_path)
        self.assertEqual("feed.xml", feed_jobs[1].feed_relative_path)
        self.assertEqual("comic", feed_jobs[1].comic_page_relative_path)

    def test_build_combined_rss_comic_data_dicts_adds_per_item_path_overrides(self):
        main_result = models.ComicBuildResult(
            comic_folder="",
            comic_info=self.make_comic_info(comic_name="Main Comic"),
            comic_data_dicts=[{"page_name": "Main"}],
            global_values={},
        )
        extra_result = models.ComicBuildResult(
            comic_folder="extras/story/",
            comic_info=self.make_comic_info(comic_name="Extra Comic"),
            comic_data_dicts=[{"page_name": "Extra"}],
            global_values={},
        )

        combined_comic_data_dicts = build_rss_feed.build_combined_rss_comic_data_dicts(
            self.make_root_comic_info("combined"),
            [extra_result, main_result],
        )

        self.assertEqual("extras/story/comic", combined_comic_data_dicts[0]["rss_comic_page_relative_path"])
        self.assertEqual("comic", combined_comic_data_dicts[1]["rss_comic_page_relative_path"])
        self.assertEqual("Extra", combined_comic_data_dicts[0]["page_name"])
        self.assertEqual("Main", combined_comic_data_dicts[1]["page_name"])

    def test_build_combined_rss_comic_data_dicts_keeps_default_titles_without_title_format(self):
        root_comic_info = self.make_root_comic_info("combined")
        main_result = models.ComicBuildResult(
            comic_folder="",
            comic_info=self.make_comic_info(comic_name="Main Comic"),
            comic_data_dicts=[{"page_name": "Main", "_title": "Main Title", "page_title": "Main Title"}],
            global_values={},
        )
        extra_result = models.ComicBuildResult(
            comic_folder="extras/story/",
            comic_info=self.make_comic_info(comic_name="Extra Comic"),
            comic_data_dicts=[{"page_name": "Extra", "_title": "Extra Title", "page_title": "Extra Title"}],
            global_values={},
        )

        combined_comic_data_dicts = build_rss_feed.build_combined_rss_comic_data_dicts(
            root_comic_info,
            [extra_result, main_result],
        )

        self.assertEqual("Extra Title", combined_comic_data_dicts[0]["_title"])
        self.assertEqual("Main Title", combined_comic_data_dicts[1]["_title"])

    def test_build_combined_rss_comic_data_dicts_applies_custom_title_format_to_extra_titles(self):
        root_comic_info = self.make_root_comic_info(
            "combined",
            rss_title_format="[{comic_title}] {page_title}",
        )
        extra_result = models.ComicBuildResult(
            comic_folder="extras/story/",
            comic_info=self.make_comic_info(comic_name="Extra Comic"),
            comic_data_dicts=[{"page_name": "Extra", "_title": "Extra Title", "page_title": "Extra Title"}],
            global_values={},
        )

        combined_comic_data_dicts = build_rss_feed.build_combined_rss_comic_data_dicts(root_comic_info, [extra_result])

        self.assertEqual("[Extra Comic] Extra Title", combined_comic_data_dicts[0]["_title"])

    def test_build_combined_rss_comic_data_dicts_rejects_unknown_title_format_variables(self):
        root_comic_info = self.make_root_comic_info(
            "combined",
            rss_title_format="{unknown} {page_title}",
        )
        extra_result = models.ComicBuildResult(
            comic_folder="extras/story/",
            comic_info=self.make_comic_info(comic_name="Extra Comic"),
            comic_data_dicts=[{"page_name": "Extra", "_title": "Extra Title", "page_title": "Extra Title"}],
            global_values={},
        )

        with self.assertRaisesRegex(ValueError, "Unknown RSS title format variable 'unknown'"):
            build_rss_feed.build_combined_rss_comic_data_dicts(root_comic_info, [extra_result])

    def test_get_rss_feed_jobs_returns_single_combined_job(self):
        root_comic_info = self.make_root_comic_info("combined")
        main_result = models.ComicBuildResult(
            comic_folder="",
            comic_info=self.make_comic_info(),
            comic_data_dicts=[{"page_name": "Main"}],
            global_values={},
        )
        extra_result = models.ComicBuildResult(
            comic_folder="extras/story/",
            comic_info=self.make_comic_info(),
            comic_data_dicts=[{"page_name": "Extra"}],
            global_values={},
        )

        feed_jobs = build_rss_feed.get_rss_feed_jobs(root_comic_info, [extra_result, main_result])

        self.assertEqual(1, len(feed_jobs))
        self.assertEqual("feed.xml", feed_jobs[0].feed_relative_path)
        self.assertEqual("comic", feed_jobs[0].comic_page_relative_path)
        self.assertEqual(2, len(feed_jobs[0].comic_data_dicts))
        self.assertEqual("extras/story/comic", feed_jobs[0].comic_data_dicts[0]["rss_comic_page_relative_path"])
        self.assertEqual("comic", feed_jobs[0].comic_data_dicts[1]["rss_comic_page_relative_path"])
        self.assertTrue(feed_jobs[0].build_enabled)

    def test_get_rss_feed_jobs_combined_uses_root_metadata_even_if_root_feed_disabled(self):
        root_comic_info = self.make_root_comic_info("combined", build_rss_feed=False)
        main_result = models.ComicBuildResult(
            comic_folder="",
            comic_info=self.make_comic_info(build_rss_feed=False),
            comic_data_dicts=[{"page_name": "Main"}],
            global_values={},
        )
        extra_result = models.ComicBuildResult(
            comic_folder="extras/story/",
            comic_info=self.make_comic_info(),
            comic_data_dicts=[{"page_name": "Extra"}],
            global_values={},
        )

        feed_jobs = build_rss_feed.get_rss_feed_jobs(root_comic_info, [extra_result, main_result])

        self.assertEqual(1, len(feed_jobs))
        self.assertIs(root_comic_info, feed_jobs[0].comic_info)
        self.assertTrue(feed_jobs[0].build_enabled)
