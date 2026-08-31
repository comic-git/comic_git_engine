import os
from configparser import RawConfigParser
from copy import deepcopy
from unittest import TestCase
from unittest.mock import mock_open, patch
from xml.etree import ElementTree

import core.models as models
from build.content.page_models import ComicImage, ComicPage
from integrations import rss


def make_image(
        filename: str = "page.png",
        alt_text: str = "Image alt",
        web_path: str | None = None,
) -> ComicImage:
    return ComicImage(
        id=f"main/Page 1/{filename}",
        filename=filename,
        source_path=filename,
        web_path=web_path or f"your_content/comics/Page 1/{filename}",
        title=filename,
        alt_text=alt_text,
    )


def make_page(page_name: str = "Page 1", **overrides) -> ComicPage:
    values = {
        "id": f"main/{page_name}",
        "comic_id": "main",
        "comic_folder": "",
        "page_name": page_name,
        "page_dir": f"your_content/comics/{page_name}/",
        "url": f"/comic/{page_name}/",
        "title": f"{page_name} Title",
        "post_date": "1903-01-01",
        "display_post_date": "January 1, 1903",
        "archive_post_date": "January 1, 1903",
        "images": [make_image()],
        "storyline": "Volume 1",
        "characters": ["Alice", "Bob"],
        "tags": ["blood", "gore"],
        "post_html": "<p>Post text</p>",
    }
    values.update(overrides)
    return ComicPage(**values)


def make_comic_info(
        *,
        comic_name: str = "The Comic",
        build: bool = True,
        combine: bool = False,
        title_format: str = "",
) -> RawConfigParser:
    comic_info = RawConfigParser()
    comic_info.add_section("Comic Info")
    comic_info.set("Comic Info", "Comic name", comic_name)
    comic_info.set("Comic Info", "Author", "The Author")
    comic_info.set("Comic Info", "Description", "The Description")
    comic_info.add_section("Comic Settings")
    comic_info.set("Comic Settings", "Date format", "%B %d, %Y")
    comic_info.set("Comic Settings", "Comic domain", "www.example.com")
    comic_info.set("Comic Settings", "Comic subdirectory", "")
    comic_info.add_section("RSS Feed")
    comic_info.set("RSS Feed", "Build RSS feed", str(build))
    comic_info.set("RSS Feed", "Description", "Feed Description")
    if combine:
        comic_info.set("RSS Feed", "Combine with Main RSS Feed", "True")
    if title_format:
        comic_info.set("RSS Feed", "RSS title format", title_format)
    return comic_info


class TestRssFeed(TestCase):
    def setUp(self):
        self.comic_info = make_comic_info()

    def build_feed_output(
            self,
            pages: list[ComicPage] | None = None,
            comic_info: RawConfigParser | None = None,
            output_dir: str | None = "",
            feed_relative_path: str = "feed.xml",
            comic_page_relative_path: str = "comic",
    ):
        pages = [make_page()] if pages is None else pages
        comic_info = deepcopy(self.comic_info) if comic_info is None else comic_info
        env_patch = {} if output_dir is None else {"OUTPUT_DIR": output_dir}
        with patch("builtins.open", new_callable=mock_open) as open_mock:
            with patch.dict(os.environ, env_patch, clear=False):
                rss.build_rss_feed(
                    comic_info,
                    pages,
                    feed_relative_path=feed_relative_path,
                    comic_page_relative_path=comic_page_relative_path,
                )
        if not open_mock.called:
            return None, None, open_mock
        return (
            open_mock.call_args.args[0],
            open_mock().write.call_args.args[0].decode("utf-8"),
            open_mock,
        )

    @staticmethod
    def get_channel(xml_text: str):
        return ElementTree.fromstring(xml_text).find("channel")

    def test_build_rss_feed_uses_structured_images_and_resolved_alt_text(self):
        page = make_page(images=[
            make_image("one.png", 'First "alt"'),
            make_image("two.png", "Second alt"),
        ])

        _, output, _ = self.build_feed_output([page])

        channel = self.get_channel(output)
        item = channel.find("item")
        self.assertEqual("Page 1 Title", item.find("title").text)
        self.assertEqual("Thu, 01 Jan 1903 00:00:00 +0000", item.find("pubDate").text)
        description = item.find("description").text
        self.assertIn('src="https://www.example.com/your_content/comics/Page 1/one.png"', description)
        self.assertIn('alt="First &quot;alt&quot;"', description)
        self.assertIn('alt="Second alt"', description)
        self.assertNotIn("alt_text=", description)
        self.assertIn("<p>Post text</p>", description)

    def test_build_rss_feed_keeps_one_item_per_multi_image_page(self):
        page = make_page(images=[make_image("one.png"), make_image("two.png")])

        _, output, _ = self.build_feed_output([page])

        self.assertEqual(1, len(self.get_channel(output).findall("item")))

    def test_build_rss_feed_keeps_no_image_page_post(self):
        page = make_page(images=[], post_html="<p>Words only</p>")

        _, output, _ = self.build_feed_output([page])

        description = self.get_channel(output).find("item/description").text
        self.assertEqual("<p>Words only</p>", description)
        self.assertNotIn("<img", description)

    def test_build_rss_feed_keeps_image_only_page(self):
        page = make_page(post_html="")

        _, output, _ = self.build_feed_output([page])

        description = self.get_channel(output).find("item/description").text
        self.assertIn("<img", description)
        self.assertNotIn("<hr>", description)

    def test_build_rss_feed_preserves_categories(self):
        _, output, _ = self.build_feed_output()

        categories = [
            (element.attrib["type"], element.text)
            for element in self.get_channel(output).findall("item/category")
        ]
        self.assertEqual(
            [
                ("storyline", "Volume 1"),
                ("character", "Alice"),
                ("character", "Bob"),
                ("tag", "blood"),
                ("tag", "gore"),
            ],
            categories,
        )

    def test_build_rss_feed_without_optional_categories(self):
        page = make_page(storyline="", characters=[], tags=[])

        _, output, _ = self.build_feed_output([page])

        self.assertEqual([], self.get_channel(output).findall("item/category"))

    def test_build_rss_feed_newest_first_reverses_without_mutating_pages(self):
        pages = [
            make_page("First", display_post_date="January 1, 1903"),
            make_page("Second", display_post_date="January 2, 1903"),
        ]
        comic_info = deepcopy(self.comic_info)
        comic_info.set("RSS Feed", "Newest first", "True")

        _, output, _ = self.build_feed_output(pages, comic_info)

        titles = [item.find("title").text for item in self.get_channel(output).findall("item")]
        self.assertEqual(["Second Title", "First Title"], titles)
        self.assertEqual(["First", "Second"], [page.page_name for page in pages])

    def test_build_rss_feed_preserves_input_order_by_default(self):
        pages = [make_page("First"), make_page("Second")]

        _, output, _ = self.build_feed_output(pages)

        titles = [item.find("title").text for item in self.get_channel(output).findall("item")]
        self.assertEqual(["First Title", "Second Title"], titles)

    def test_build_rss_feed_allows_empty_page_list(self):
        _, output, _ = self.build_feed_output([])

        self.assertEqual([], self.get_channel(output).findall("item"))

    def test_build_rss_feed_rejects_duplicate_page_names(self):
        with self.assertRaisesRegex(ValueError, "Duplicate page_name 'Same'"):
            self.build_feed_output([make_page("Same"), make_page("Same")])

    def test_build_rss_feed_preserves_absolute_image_url(self):
        page = make_page(images=[make_image(web_path="https://cdn.example.com/page.png")])

        _, output, _ = self.build_feed_output([page])

        description = self.get_channel(output).find("item/description").text
        self.assertIn('src="https://cdn.example.com/page.png"', description)

    def test_build_rss_feed_uses_custom_output_and_route_paths(self):
        path, output, _ = self.build_feed_output(
            output_dir="output",
            feed_relative_path="extras/news.xml",
            comic_page_relative_path="extras/bonus/comic",
        )

        channel = self.get_channel(output)
        self.assertEqual(os.path.join("output", "extras/news.xml"), path)
        self.assertEqual(
            "https://www.example.com/extras/bonus/comic/Page 1/",
            channel.find("item/link").text,
        )

    def test_build_rss_feed_job_supports_per_page_route_override(self):
        feed_page = rss.FeedPage(
            page=make_page("Extra"),
            title="Extra Title",
            comic_page_relative_path="extras/story/comic",
        )
        job = rss.FeedJob(self.comic_info, [feed_page], build_enabled=True)
        with patch("builtins.open", new_callable=mock_open) as open_mock:
            rss.build_rss_feed_from_job(job)

        output = open_mock().write.call_args.args[0].decode("utf-8")
        self.assertEqual(
            "https://www.example.com/extras/story/comic/Extra/",
            self.get_channel(output).find("item/link").text,
        )

    def test_build_rss_feed_skips_write_when_disabled(self):
        comic_info = deepcopy(self.comic_info)
        comic_info.set("RSS Feed", "Build RSS feed", "False")

        feed_path, output, open_mock = self.build_feed_output(comic_info=comic_info)

        self.assertIsNone(feed_path)
        self.assertIsNone(output)
        open_mock.assert_not_called()

    def test_build_rss_feed_uses_default_hidden_settings(self):
        comic_info = deepcopy(self.comic_info)
        for option in ("Description", "Language", "Image", "Image width", "Image height"):
            comic_info.remove_option("RSS Feed", option)

        _, output, _ = self.build_feed_output(comic_info=comic_info)

        channel = self.get_channel(output)
        self.assertEqual("The Description", channel.find("description").text)
        self.assertEqual("en-us", channel.find("language").text)
        self.assertEqual(
            "https://www.example.com/your_content/images/banner.png",
            channel.find("image/url").text,
        )

    def test_build_rss_feed_invalid_post_date_is_helpful(self):
        page = make_page(display_post_date="not a date")

        with self.assertRaisesRegex(ValueError, "Invalid post date 'not a date' for page 'Page 1'"):
            self.build_feed_output([page])

    def test_build_rss_feed_write_error_is_helpful(self):
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            with patch.dict(os.environ, {"OUTPUT_DIR": "output"}, clear=False):
                with self.assertRaisesRegex(ValueError, "Could not write RSS feed"):
                    rss.build_rss_feed(self.comic_info, [make_page()])


class TestRssFeedJobs(TestCase):
    @staticmethod
    def result(
            comic_folder: str,
            comic_info: RawConfigParser,
            pages: list[ComicPage],
    ) -> models.ComicBuildResult:
        return models.ComicBuildResult(comic_folder, comic_info, pages, {})

    def test_build_job_for_extra_comic_uses_folder_paths_and_title_format(self):
        comic_info = make_comic_info(
            comic_name="Extra Comic",
            title_format="{comic_title}: {page_title}",
        )
        result = self.result("extras/story/", comic_info, [make_page(title="Page Title")])

        job = rss.build_rss_feed_job_for_comic_result(result)

        self.assertEqual("extras/story/feed.xml", job.feed_relative_path)
        self.assertEqual("extras/story/comic", job.comic_page_relative_path)
        self.assertEqual("Extra Comic: Page Title", job.pages[0].title)
        self.assertIs(result.pages[0], job.pages[0].page)

    def test_build_main_feed_pages_adds_extra_route_and_owner_title_format(self):
        main = self.result(
            "",
            make_comic_info(comic_name="Main", title_format="[{comic_title}] {page_title}"),
            [make_page("Main Page", title="Main Title")],
        )
        extra = self.result(
            "extras/story/",
            make_comic_info(comic_name="Extra", title_format="{comic_title}: {page_title}"),
            [make_page("Extra Page", title="Extra Title")],
        )

        pages = rss.build_main_rss_feed_pages(main, [extra])

        self.assertEqual("[Main] Main Title", pages[0].title)
        self.assertIsNone(pages[0].comic_page_relative_path)
        self.assertEqual("Extra: Extra Title", pages[1].title)
        self.assertEqual("extras/story/comic", pages[1].comic_page_relative_path)

    def test_title_format_rejects_unknown_variables(self):
        result = self.result(
            "",
            make_comic_info(title_format="{unknown} {page_title}"),
            [make_page()],
        )

        with self.assertRaisesRegex(ValueError, "Unknown RSS title format variable 'unknown'"):
            rss.build_feed_pages_for_comic_result(result)

    def test_get_jobs_returns_combined_main_and_standalone_extra_feeds(self):
        main = self.result("", make_comic_info(comic_name="Main"), [make_page("Main")])
        combined = self.result(
            "extras/story/",
            make_comic_info(comic_name="Combined", combine=True),
            [make_page("Combined")],
        )
        standalone = self.result(
            "extras/solo/",
            make_comic_info(comic_name="Solo"),
            [make_page("Solo")],
        )

        jobs = rss.get_rss_feed_jobs([combined, standalone, main])

        self.assertEqual(["feed.xml", "extras/solo/feed.xml"], [job.feed_relative_path for job in jobs])
        self.assertEqual(["Main", "Combined"], [feed_page.page.page_name for feed_page in jobs[0].pages])
        self.assertEqual("extras/story/comic", jobs[0].pages[1].comic_page_relative_path)

    def test_get_jobs_filters_disabled_extras(self):
        main = self.result("", make_comic_info(), [make_page("Main")])
        disabled = self.result(
            "extras/off/",
            make_comic_info(build=False, combine=True),
            [make_page("Off")],
        )

        jobs = rss.get_rss_feed_jobs([disabled, main])

        self.assertEqual(1, len(jobs))
        self.assertEqual(["Main"], [feed_page.page.page_name for feed_page in jobs[0].pages])

    def test_get_jobs_skips_combined_extras_when_main_feed_disabled(self):
        main = self.result("", make_comic_info(build=False), [make_page("Main")])
        extra = self.result(
            "extras/story/",
            make_comic_info(combine=True),
            [make_page("Extra")],
        )

        self.assertEqual([], rss.get_rss_feed_jobs([extra, main]))

    def test_inherited_combine_setting_can_be_overridden(self):
        root_info = make_comic_info(combine=True)
        main = self.result("", root_info, [make_page("Main")])
        extra_info = deepcopy(root_info)
        extra_info.set("Comic Info", "Comic name", "Extra")
        extra_info.set("RSS Feed", "Combine with Main RSS Feed", "False")
        extra = self.result("extras/story/", extra_info, [make_page("Extra")])

        jobs = rss.get_rss_feed_jobs([extra, main])

        self.assertEqual(["feed.xml", "extras/story/feed.xml"], [job.feed_relative_path for job in jobs])
