import os
from configparser import RawConfigParser
from unittest import TestCase
from unittest.mock import MagicMock, call, patch

import core.models as models
from build import build_site
from build import site_builder
from build.content.page_models import ArchiveEntryMode, ComicImage, ComicPage


COMIC_URL = "https://ryanvilbrandt.github.io/comic_git_dev"
MUT = "build.build_site."


def get_mock_dict(mocks):
    return {mock._mock_name: mock for mock in mocks}


@patch(MUT + "print_processing_times")
@patch(MUT + "checkpoint")
@patch(MUT + "copy_site_root_files")
@patch(MUT + "copy_output_assets")
@patch(MUT + "write_cms_admin")
@patch(MUT + "build_rss_feed_from_job")
@patch(MUT + "get_rss_feed_jobs", return_value=[])
@patch(MUT + "build_and_publish_comic_pages", return_value=([{"page_name": "Page 1"}], {"theme": "default"}))
@patch(MUT + "get_extra_comics_list", return_value=[])
@patch(MUT + "setup_output_file_space")
@patch(MUT + "run_hook", return_value=None)
@patch(MUT + "utils.get_comic_url", return_value=(COMIC_URL, "/comic_git_dev"))
@patch(MUT + "load_main_comic_info")
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
        m["load_main_comic_info"].return_value = comic_info
        pages = [{"page_name": "Page 1"}]
        global_values = {"theme": "default"}
        m["build_and_publish_comic_pages"].return_value = (pages, global_values)
        feed_job = object()
        m["get_rss_feed_jobs"].return_value = [feed_job]

        build_site.main()

        m["get_rss_feed_jobs"].assert_called_once_with(
            [models.ComicBuildResult("", comic_info, pages, global_values)]
        )
        m["build_rss_feed_from_job"].assert_called_once_with(feed_job)
        m["copy_output_assets"].assert_called_once_with("build")
        m["copy_site_root_files"].assert_called_once_with("build")
        cms_settings = m["write_cms_admin"].call_args.args[0]
        self.assertFalse(cms_settings.enabled)
        m["write_cms_admin"].assert_called_once_with(cms_settings, [], "build")

    @patch(MUT + "os.makedirs")
    @patch(MUT + "get_extra_comic_info")
    def test_main_builds_extra_comics_before_main_comic(self, *_mocks):
        m = get_mock_dict(_mocks)
        comic_info = self.make_comic_info()
        extra_comic_info = self.make_comic_info()
        m["load_main_comic_info"].return_value = comic_info
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
        m["load_main_comic_info"].return_value = self.make_comic_info()

        build_site.main()

        m["copy_output_assets"].assert_called_once_with("build")
        m["copy_site_root_files"].assert_called_once_with("build")

    def test_main_copies_output_assets_when_output_dir_is_set(self, *_mocks):
        m = get_mock_dict(_mocks)
        m["load_main_comic_info"].return_value = self.make_comic_info()

        with patch.dict("os.environ", {"OUTPUT_DIR": "output"}, clear=False):
            build_site.main()

        m["copy_output_assets"].assert_called_once_with("output")
        m["copy_site_root_files"].assert_called_once_with("output")

    def test_main_skips_copying_output_assets_when_output_dir_is_explicitly_blank(self, *_mocks):
        m = get_mock_dict(_mocks)
        m["load_main_comic_info"].return_value = self.make_comic_info()

        with patch.dict("os.environ", {"OUTPUT_DIR": ""}, clear=False):
            build_site.main()

        m["copy_output_assets"].assert_not_called()
        m["copy_site_root_files"].assert_called_once_with("")

    def test_main_records_checkpoint_after_copying_site_root_files(self, *_mocks):
        m = get_mock_dict(_mocks)
        m["load_main_comic_info"].return_value = self.make_comic_info()

        build_site.main()

        m["copy_site_root_files"].assert_called_once_with("build")
        self.assertIn(call("Copy site_root files"), m["checkpoint"].call_args_list)
        self.assertIn(call("Build CMS admin"), m["checkpoint"].call_args_list)

    @patch(MUT + "os.path.isfile", return_value=True)
    def test_main_generates_local_cms_after_site_root_and_before_postprocess(self, *_mocks):
        m = get_mock_dict(_mocks)
        comic_info = self.make_comic_info()
        comic_info.add_section("CMS")
        comic_info.set("CMS", "Enabled", "True")
        m["load_main_comic_info"].return_value = comic_info
        manager = MagicMock()
        manager.attach_mock(m["copy_site_root_files"], "copy_site_root")
        manager.attach_mock(m["write_cms_admin"], "write_cms")
        manager.attach_mock(m["run_hook"], "run_hook")

        build_site.main(cms_local_backend=True)

        write_call = next(item for item in manager.mock_calls if item[0] == "write_cms")
        settings, collections, output_dir = write_call.args
        self.assertTrue(settings.local_backend)
        self.assertEqual(["main_comic_pages"], [collection.name for collection in collections])
        self.assertEqual("build", output_dir)
        call_names = [item[0] for item in manager.mock_calls]
        self.assertLess(call_names.index("copy_site_root"), call_names.index("write_cms"))
        postprocess_index = next(
            index
            for index, item in enumerate(manager.mock_calls)
            if item[0] == "run_hook" and item.args[1] == "postprocess"
        )
        self.assertLess(call_names.index("write_cms"), postprocess_index)

    def test_main_surfaces_missing_site_root_folder(self, *_mocks):
        m = get_mock_dict(_mocks)
        m["load_main_comic_info"].return_value = self.make_comic_info()
        m["copy_site_root_files"].side_effect = FileNotFoundError("your_content/site_root")

        with self.assertRaisesRegex(FileNotFoundError, "your_content/site_root"):
            build_site.main()

    def test_main_surfaces_build_failures(self, *_mocks):
        m = get_mock_dict(_mocks)
        m["load_main_comic_info"].return_value = self.make_comic_info()
        m["build_and_publish_comic_pages"].side_effect = RuntimeError("build failed")

        with self.assertRaisesRegex(RuntimeError, "build failed"):
            build_site.main()


class TestCliArgs(TestCase):

    def test_parse_args_reads_output_dir(self):
        args = build_site.parse_args(["--output-dir", "preview_site"])

        self.assertEqual("preview_site", args.output_dir)
        self.assertFalse(args.delete_scheduled_posts)
        self.assertFalse(args.publish_all_comics)
        self.assertFalse(args.cms_local_backend)

    def test_parse_args_reads_cms_local_backend(self):
        args = build_site.parse_args(["--cms-local-backend"])

        self.assertTrue(args.cms_local_backend)

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


class TestArchiveStorylines(TestCase):
    def make_config(self, mode=ArchiveEntryMode.PAGES, show_text_only_posts=None):
        config = RawConfigParser()
        config.add_section("Archive")
        config.set("Archive", "List images separately", str(mode == ArchiveEntryMode.IMAGES))
        config.set("Archive", "Show Uncategorized comics", "True")
        if show_text_only_posts is not None:
            config.set("Archive", "Show text-only posts", str(show_text_only_posts))
        config.add_section("Comic Settings")
        config.set("Comic Settings", "Theme", "default")
        return config

    def make_page(self, name="001", images=2):
        comic_images = [
            ComicImage(
                id=f"main/{name}/page-{index}.png",
                filename=f"page-{index}.png",
                source_path=f"page-{index}.png",
                web_path=f"your_content/comics/{name}/page-{index}.png",
                title=f"Image {index}",
                alt_text="",
                thumbnail_path=f"thumb-{index}.jpg",
            )
            for index in range(images)
        ]
        return ComicPage(
            id=f"main/{name}",
            comic_id="main",
            comic_folder="",
            page_name=name,
            page_dir=f"your_content/comics/{name}/",
            url=f"/comic/{name}/",
            title=f"Page {name}",
            post_date="2024-01-01",
            display_post_date="January 01, 2024",
            archive_post_date="Jan 1",
            images=comic_images,
            thumbnail_path="page-thumb.jpg",
            storyline="Arc",
        )

    @patch("build.site_builder.run_hook", return_value=None)
    def test_page_mode_is_default_and_emits_one_entry_per_page(self, mock_hook):
        page = self.make_page()
        storylines = site_builder.get_storylines(self.make_config(), [page])

        self.assertEqual(1, len(storylines["Arc"]))
        entry = storylines["Arc"][0]
        self.assertEqual("Page 001", entry.title)
        self.assertEqual("page-thumb.jpg", entry.thumbnail_path)
        self.assertIsNone(entry.image)
        self.assertEqual(1, entry.image_index)
        self.assertIs(page, mock_hook.call_args.args[2][1][0])
        self.assertIs(entry, mock_hook.call_args.args[2][2]["Arc"][0])

    @patch("build.site_builder.run_hook", return_value=None)
    def test_image_mode_emits_ordered_direct_image_entries(self, _mock_hook):
        storylines = site_builder.get_storylines(
            self.make_config(ArchiveEntryMode.IMAGES),
            [self.make_page()],
        )

        self.assertEqual(["Image 0", "Image 1"], [entry.title for entry in storylines["Arc"]])
        self.assertEqual([1, 2], [entry.image_index for entry in storylines["Arc"]])

    @patch("build.site_builder.run_hook", return_value=None)
    def test_image_mode_retains_one_entry_for_no_image_page(self, _mock_hook):
        storylines = site_builder.get_storylines(
            self.make_config(ArchiveEntryMode.IMAGES),
            [self.make_page(images=0)],
        )

        self.assertEqual(1, len(storylines["Arc"]))
        self.assertIsNone(storylines["Arc"][0].image)
        self.assertIsNone(storylines["Arc"][0].image_index)

    @patch("build.site_builder.run_hook", return_value=None)
    def test_image_mode_can_exclude_text_only_pages_without_empty_storylines(self, _mock_hook):
        page = self.make_page(images=0)
        page.storyline = "Text only arc"

        storylines = site_builder.get_storylines(
            self.make_config(ArchiveEntryMode.IMAGES, show_text_only_posts=False),
            [page],
        )

        self.assertNotIn("Text only arc", storylines)
        self.assertEqual({}, storylines)

    @patch("build.site_builder.run_hook", return_value=None)
    def test_page_mode_ignores_show_text_only_posts(self, _mock_hook):
        storylines = site_builder.get_storylines(
            self.make_config(ArchiveEntryMode.PAGES, show_text_only_posts=False),
            [self.make_page(images=0)],
        )

        self.assertEqual(1, len(storylines["Arc"]))
        self.assertIsNone(storylines["Arc"][0].image_index)

    @patch("build.site_builder.run_hook", return_value=None)
    def test_text_only_setting_is_isolated_per_comic_config(self, _mock_hook):
        page = self.make_page(images=0)

        hidden = site_builder.get_storylines(
            self.make_config(ArchiveEntryMode.IMAGES, show_text_only_posts=False),
            [page],
        )
        shown = site_builder.get_storylines(
            self.make_config(ArchiveEntryMode.IMAGES),
            [page],
        )

        self.assertEqual({}, hidden)
        self.assertEqual(1, len(shown["Arc"]))

    @patch("build.site_builder.run_hook", return_value=None)
    def test_uncategorized_pages_can_be_hidden(self, _mock_hook):
        config = self.make_config()
        config.set("Archive", "Show Uncategorized comics", "False")
        page = self.make_page()
        page.storyline = ""

        storylines = site_builder.get_storylines(config, [page])

        self.assertEqual({}, storylines)

    @patch("build.site_builder.run_hook", return_value=None)
    def test_uncategorized_storyline_is_listed_last(self, _mock_hook):
        uncategorized = self.make_page("001")
        uncategorized.storyline = ""
        categorized = self.make_page("002")

        storylines = site_builder.get_storylines(
            self.make_config(),
            [uncategorized, categorized],
        )

        self.assertEqual(["Arc", "Uncategorized"], list(storylines))


class TestInfiniteScrollChapters(TestCase):
    def make_config(self, show_uncategorized=True):
        config = RawConfigParser()
        config.add_section("Archive")
        config.set("Archive", "List images separately", "True")
        config.set("Archive", "Show text-only posts", "False")
        config.set("Archive", "Show Uncategorized comics", str(show_uncategorized))
        return config

    def make_page(self, name, storyline, has_images):
        images = []
        if has_images:
            images.append(ComicImage(
                id=f"main/{name}/page.png",
                filename="page.png",
                source_path="page.png",
                web_path=f"your_content/comics/{name}/page.png",
                title=name,
                alt_text="",
            ))
        return ComicPage(
            id=f"main/{name}",
            comic_id="main",
            comic_folder="",
            page_name=name,
            page_dir=f"your_content/comics/{name}/",
            url=f"/comic/{name}/",
            title=name,
            post_date="2024-01-01",
            display_post_date="January 01, 2024",
            archive_post_date="Jan 1",
            images=images,
            storyline=storyline,
        )

    def test_chapters_select_first_image_page_and_ignore_archive_projection_settings(self):
        text_only = self.make_page("intro", "Arc", False)
        first_image = self.make_page("001", "Arc", True)
        later_image = self.make_page("002", "Arc", True)
        uncategorized = self.make_page("bonus", "", True)

        chapters = site_builder.get_infinite_scroll_chapters(
            self.make_config(),
            [text_only, first_image, later_image, uncategorized],
        )

        self.assertIs(first_image, chapters["Arc"])
        self.assertIs(uncategorized, chapters["Uncategorized"])
        self.assertEqual(["Arc", "Uncategorized"], list(chapters))

    def test_chapters_omit_text_only_and_hidden_uncategorized_groups(self):
        chapters = site_builder.get_infinite_scroll_chapters(
            self.make_config(show_uncategorized=False),
            [
                self.make_page("intro", "Text only", False),
                self.make_page("bonus", "", True),
            ],
        )

        self.assertEqual({}, chapters)
