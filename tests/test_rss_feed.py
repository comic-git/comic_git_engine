import os
from configparser import RawConfigParser
from copy import deepcopy
from unittest import TestCase
from unittest.mock import mock_open, patch
from xml.etree import ElementTree

from scripts import build_rss_feed


class TestRssFeed(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.feed_description = "\u00ca\u20ac\u00e1\u00b4\u0153\u00c9\u00b4"
        cls.comic_info = RawConfigParser()
        cls.comic_info.add_section("Comic Info")
        cls.comic_info.set("Comic Info", "Comic name", "The Dark World of the Furry")
        cls.comic_info.set("Comic Info", "Author", "Lucifer, Prince of Lies")
        cls.comic_info.add_section("Comic Settings")
        cls.comic_info.set("Comic Settings", "Date format", "%B %d, %Y")
        cls.comic_info.set("Comic Settings", "Comic domain", "www.tamberlanecomic.com")
        cls.comic_info.set("Comic Settings", "Comic subdirectory", "")
        cls.comic_info.add_section("RSS Feed")
        cls.comic_info.set("RSS Feed", "Build RSS feed", "True")
        cls.comic_info.set("RSS Feed", "Description", cls.feed_description)
        cls.comic_info.set("RSS Feed", "Language", "en")
        cls.comic_info.set("RSS Feed", "Image", "rss_banner.png")
        cls.comic_info.set("RSS Feed", "Image width", "100")
        cls.comic_info.set("RSS Feed", "Image height", "32")

    def setUp(self):
        self.maxDiff = None

    def make_comic_data(self, **overrides):
        data = {
            "_title": "I'ma title bay-bee!",
            "_post_date": "January 1, 1903",
            "page_name": "Page 1",
            "comic_paths": ["your_content/comics/Page 1/page_1.png"],
            "_storyline": "Volume 1",
            "_characters": ["Alice", "Bob", "Charlie", "Dennis"],
            "_tags": ["blood", "gore", "sex", "violence"],
            "escaped_alt_text": "Ayo lookit the title on this bitch",
            "post_html": "<p>Why you reading this when there's a perfectly good image up above?</p>",
        }
        data.update(overrides)
        return data

    def build_feed_output(
            self,
            comic_data_dicts=None,
            comic_info=None,
            output_dir="",
            feed_relative_path="feed.xml",
            comic_page_relative_path="comic",
    ):
        if comic_data_dicts is None:
            comic_data_dicts = [self.make_comic_data()]
        if comic_info is None:
            comic_info = deepcopy(self.comic_info)
        with patch("builtins.open", new_callable=mock_open) as open_mock:
            with patch.dict(os.environ, {"OUTPUT_DIR": output_dir}, clear=False):
                build_rss_feed.build_rss_feed(
                    comic_info,
                    comic_data_dicts,
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
    def parse_feed(xml_text):
        return ElementTree.fromstring(xml_text)

    def get_items(self, xml_text):
        root = self.parse_feed(xml_text)
        channel = root.find("channel")
        return channel.findall("item")

    def test_build_rss_feed(self):
        _, actual, _ = self.build_feed_output()

        expected = f"""<?xml version="1.0" ?>
<rss xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/" version="2.0">
    <channel>
        <atom:link href="https://www.tamberlanecomic.com/feed.xml" rel="self" type="application/rss+xml"/>
        <title>The Dark World of the Furry</title>
        <description>{self.feed_description}</description>
        <link>https://www.tamberlanecomic.com/</link>
        <dc:creator>Lucifer, Prince of Lies</dc:creator>
        <language>en</language>
        <image>
            <title>The Dark World of the Furry</title>
            <link>https://www.tamberlanecomic.com/</link>
            <url>https://www.tamberlanecomic.com/rss_banner.png</url>
            <width>100</width>
            <height>32</height>
        </image>
        <item>
            <title>I'ma title bay-bee!</title>
            <dc:creator>Lucifer, Prince of Lies</dc:creator>
            <pubDate>Thu, 01 Jan 1903 00:00:00 +0000</pubDate>
            <link>https://www.tamberlanecomic.com/comic/Page 1/</link>
            <guid isPermaLink="true">https://www.tamberlanecomic.com/comic/page_1/</guid>
            <category type="storyline">Volume 1</category>
            <category type="character">Alice</category>
            <category type="character">Bob</category>
            <category type="character">Charlie</category>
            <category type="character">Dennis</category>
            <category type="tag">blood</category>
            <category type="tag">gore</category>
            <category type="tag">sex</category>
            <category type="tag">violence</category>
            <description><![CDATA[<p><img src="https://www.tamberlanecomic.com/your_content/comics/Page 1/page_1.png" alt_text="Ayo lookit the title on this bitch"></p>

<hr>

<p>Why you reading this when there's a perfectly good image up above?</p>]]></description>
        </item>
    </channel>
</rss>
"""
        self.assertEqual(expected, actual)

    def test_build_rss_feed_subdirectory(self):
        comic_info = deepcopy(self.comic_info)
        comic_info.set("Comic Settings", "Comic domain", "JacobWG.github.io")
        comic_info.set("Comic Settings", "Comic subdirectory", "bestcomic")

        _, actual, _ = self.build_feed_output(comic_info=comic_info)

        expected = f"""<?xml version="1.0" ?>
<rss xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/" version="2.0">
    <channel>
        <atom:link href="https://JacobWG.github.io/bestcomic/feed.xml" rel="self" type="application/rss+xml"/>
        <title>The Dark World of the Furry</title>
        <description>{self.feed_description}</description>
        <link>https://JacobWG.github.io/bestcomic/</link>
        <dc:creator>Lucifer, Prince of Lies</dc:creator>
        <language>en</language>
        <image>
            <title>The Dark World of the Furry</title>
            <link>https://JacobWG.github.io/bestcomic/</link>
            <url>https://JacobWG.github.io/bestcomic/rss_banner.png</url>
            <width>100</width>
            <height>32</height>
        </image>
        <item>
            <title>I'ma title bay-bee!</title>
            <dc:creator>Lucifer, Prince of Lies</dc:creator>
            <pubDate>Thu, 01 Jan 1903 00:00:00 +0000</pubDate>
            <link>https://JacobWG.github.io/bestcomic/comic/Page 1/</link>
            <guid isPermaLink="true">https://jacobwg.github.io/bestcomic/comic/page_1/</guid>
            <category type="storyline">Volume 1</category>
            <category type="character">Alice</category>
            <category type="character">Bob</category>
            <category type="character">Charlie</category>
            <category type="character">Dennis</category>
            <category type="tag">blood</category>
            <category type="tag">gore</category>
            <category type="tag">sex</category>
            <category type="tag">violence</category>
            <description><![CDATA[<p><img src="https://JacobWG.github.io/bestcomic/your_content/comics/Page 1/page_1.png" alt_text="Ayo lookit the title on this bitch"></p>

<hr>

<p>Why you reading this when there's a perfectly good image up above?</p>]]></description>
        </item>
    </channel>
</rss>
"""
        self.assertEqual(expected, actual)

    def test_build_rss_feed_skips_write_when_disabled(self):
        comic_info = deepcopy(self.comic_info)
        comic_info.set("RSS Feed", "Build RSS feed", "False")

        feed_path, output, open_mock = self.build_feed_output(comic_info=comic_info)

        self.assertIsNone(feed_path)
        self.assertIsNone(output)
        open_mock.assert_not_called()

    def test_build_rss_feed_uses_output_dir(self):
        feed_path, _, _ = self.build_feed_output(output_dir="output")

        self.assertEqual(os.path.join("output", "feed.xml"), feed_path)

    def test_build_rss_feed_uses_custom_feed_relative_path(self):
        feed_path, output, _ = self.build_feed_output(
            output_dir="output",
            feed_relative_path="extras/news.xml",
        )

        root = self.parse_feed(output)
        channel = root.find("channel")
        atom_link = channel.find("{http://www.w3.org/2005/Atom}link")

        self.assertEqual(os.path.join("output", "extras/news.xml"), feed_path)
        self.assertEqual("https://www.tamberlanecomic.com/extras/news.xml", atom_link.attrib["href"])
        self.assertEqual("https://www.tamberlanecomic.com/", channel.find("link").text)

    def test_build_rss_feed_uses_custom_comic_page_relative_path(self):
        _, output, _ = self.build_feed_output(
            comic_page_relative_path="extras/bonus/comic",
        )

        item = self.get_items(output)[0]

        self.assertEqual(
            "https://www.tamberlanecomic.com/extras/bonus/comic/Page 1/",
            item.find("link").text,
        )
        self.assertEqual(
            "https://www.tamberlanecomic.com/extras/bonus/comic/page_1/",
            item.find("guid").text,
        )

    def test_build_rss_feed_allows_per_item_comic_page_relative_path_override(self):
        comic_data_dicts = [
            self.make_comic_data(_title="Main", page_name="Main Page"),
            self.make_comic_data(
                _title="Extra",
                page_name="Extra Page",
                rss_comic_page_relative_path="extras/story/comic",
            ),
        ]

        _, output, _ = self.build_feed_output(comic_data_dicts=comic_data_dicts)
        items = self.get_items(output)

        self.assertEqual(
            "https://www.tamberlanecomic.com/comic/Main Page/",
            items[0].find("link").text,
        )
        self.assertEqual(
            "https://www.tamberlanecomic.com/extras/story/comic/Extra Page/",
            items[1].find("link").text,
        )

    def test_build_rss_feed_from_job_uses_explicit_job_settings(self):
        feed_job = build_rss_feed.build_feed_job(
            comic_info=deepcopy(self.comic_info),
            comic_data_dicts=[self.make_comic_data()],
            feed_relative_path="rss/main.xml",
            comic_page_relative_path="extras/story/comic",
        )

        with patch("builtins.open", new_callable=mock_open) as open_mock:
            with patch.dict(os.environ, {"OUTPUT_DIR": "output"}, clear=False):
                build_rss_feed.build_rss_feed_from_job(feed_job)

        feed_path = open_mock.call_args.args[0]
        output = open_mock().write.call_args.args[0].decode("utf-8")
        root = self.parse_feed(output)
        channel = root.find("channel")
        atom_link = channel.find("{http://www.w3.org/2005/Atom}link")
        item = channel.find("item")

        self.assertEqual(os.path.join("output", "rss/main.xml"), feed_path)
        self.assertEqual("https://www.tamberlanecomic.com/rss/main.xml", atom_link.attrib["href"])
        self.assertEqual("https://www.tamberlanecomic.com/extras/story/comic/Page 1/", item.find("link").text)

    def test_build_rss_feed_newest_first_reverses_item_order(self):
        comic_info = deepcopy(self.comic_info)
        comic_info.set("RSS Feed", "Newest first", "True")
        comic_data_dicts = [
            self.make_comic_data(_title="Page One", _post_date="January 1, 1903", page_name="Page 1"),
            self.make_comic_data(_title="Page Two", _post_date="January 2, 1903", page_name="Page 2"),
            self.make_comic_data(_title="Page Three", _post_date="January 3, 1903", page_name="Page 3"),
        ]

        _, output, _ = self.build_feed_output(comic_data_dicts=comic_data_dicts, comic_info=comic_info)
        titles = [item.find("title").text for item in self.get_items(output)]

        self.assertEqual(["Page Three", "Page Two", "Page One"], titles)

    def test_build_rss_feed_newest_first_does_not_mutate_input_order(self):
        comic_info = deepcopy(self.comic_info)
        comic_info.set("RSS Feed", "Newest first", "True")
        comic_data_dicts = [
            self.make_comic_data(_title="Page One", _post_date="January 1, 1903", page_name="Page 1"),
            self.make_comic_data(_title="Page Two", _post_date="January 2, 1903", page_name="Page 2"),
            self.make_comic_data(_title="Page Three", _post_date="January 3, 1903", page_name="Page 3"),
        ]

        self.build_feed_output(comic_data_dicts=comic_data_dicts, comic_info=comic_info)
        titles = [comic_data["_title"] for comic_data in comic_data_dicts]

        self.assertEqual(["Page One", "Page Two", "Page Three"], titles)

    def test_build_rss_feed_preserves_input_order_by_default(self):
        comic_data_dicts = [
            self.make_comic_data(_title="Page One", _post_date="January 1, 1903", page_name="Page 1"),
            self.make_comic_data(_title="Page Two", _post_date="January 2, 1903", page_name="Page 2"),
            self.make_comic_data(_title="Page Three", _post_date="January 3, 1903", page_name="Page 3"),
        ]

        _, output, _ = self.build_feed_output(comic_data_dicts=comic_data_dicts)
        titles = [item.find("title").text for item in self.get_items(output)]

        self.assertEqual(["Page One", "Page Two", "Page Three"], titles)

    def test_build_rss_feed_multiple_items_keep_distinct_descriptions(self):
        comic_data_dicts = [
            self.make_comic_data(
                _title="Page One",
                page_name="Page 1",
                comic_paths=["your_content/comics/Page 1/page_1.png"],
                post_html="<p>First post body.</p>",
            ),
            self.make_comic_data(
                _title="Page Two",
                page_name="Page 2",
                comic_paths=["your_content/comics/Page 2/page_2.png"],
                post_html="<p>Second post body.</p>",
            ),
        ]

        _, output, _ = self.build_feed_output(comic_data_dicts=comic_data_dicts)
        descriptions = [item.find("description").text for item in self.get_items(output)]

        self.assertEqual(
            [
                """<p><img src="https://www.tamberlanecomic.com/your_content/comics/Page 1/page_1.png" alt_text="Ayo lookit the title on this bitch"></p>

<hr>

<p>First post body.</p>""",
                """<p><img src="https://www.tamberlanecomic.com/your_content/comics/Page 2/page_2.png" alt_text="Ayo lookit the title on this bitch"></p>

<hr>

<p>Second post body.</p>""",
            ],
            descriptions,
        )

    def test_build_rss_feed_duplicate_page_name_raises_helpful_error(self):
        comic_data_dicts = [
            self.make_comic_data(_title="Page One", page_name="Duplicate Page"),
            self.make_comic_data(_title="Page Two", page_name="Duplicate Page"),
        ]

        with self.assertRaises(ValueError) as cm:
            self.build_feed_output(comic_data_dicts=comic_data_dicts)

        self.assertIn("Duplicate page_name 'Duplicate Page' found in RSS feed input.", str(cm.exception))
        self.assertIn("Each comic page in a single feed must have a unique page_name.", str(cm.exception))

    def test_build_rss_feed_without_optional_categories(self):
        comic_data = self.make_comic_data()
        del comic_data["_storyline"]
        del comic_data["_characters"]
        del comic_data["_tags"]

        _, output, _ = self.build_feed_output(comic_data_dicts=[comic_data])
        item = self.get_items(output)[0]

        self.assertEqual([], item.findall("category"))

    def test_build_rss_feed_with_empty_comic_list(self):
        _, output, _ = self.build_feed_output(comic_data_dicts=[])

        root = self.parse_feed(output)
        channel = root.find("channel")

        self.assertEqual("The Dark World of the Furry", channel.find("title").text)
        self.assertEqual([], channel.findall("item"))

    def test_build_rss_feed_multiple_images_without_alt_text(self):
        comic_data = self.make_comic_data(
            comic_paths=[
                "your_content/comics/Page 1/page_1a.png",
                "your_content/comics/Page 1/page_1b.png",
            ],
            escaped_alt_text="",
        )

        _, output, _ = self.build_feed_output(comic_data_dicts=[comic_data])
        description = self.get_items(output)[0].find("description").text

        expected = """<p><img src="https://www.tamberlanecomic.com/your_content/comics/Page 1/page_1a.png"></p>
<p><img src="https://www.tamberlanecomic.com/your_content/comics/Page 1/page_1b.png"></p>

<hr>

<p>Why you reading this when there's a perfectly good image up above?</p>"""
        self.assertEqual(expected, description)

    def test_build_rss_feed_absolute_comic_image_urls_are_preserved(self):
        comic_data = self.make_comic_data(
            comic_paths=["https://cdn.example.com/comics/page_1.png"],
        )

        _, output, _ = self.build_feed_output(comic_data_dicts=[comic_data])
        description = self.get_items(output)[0].find("description").text

        self.assertIn('<img src="https://cdn.example.com/comics/page_1.png"', description)

    def test_build_rss_feed_special_characters_in_page_name(self):
        comic_data = self.make_comic_data(page_name="Chapter 1 & 2")

        _, output, _ = self.build_feed_output(comic_data_dicts=[comic_data])
        item = self.get_items(output)[0]

        self.assertEqual("https://www.tamberlanecomic.com/comic/Chapter 1 & 2/", item.find("link").text)
        self.assertEqual("https://www.tamberlanecomic.com/comic/chapter_1___2/", item.find("guid").text)

    def test_build_rss_feed_absolute_image_url_is_preserved(self):
        comic_info = deepcopy(self.comic_info)
        comic_info.set("RSS Feed", "Image", "https://cdn.example.com/banner.png")

        _, output, _ = self.build_feed_output(comic_info=comic_info)
        root = self.parse_feed(output)
        image = root.find("channel").find("image")

        self.assertEqual("https://cdn.example.com/banner.png", image.find("url").text)

    def test_build_rss_feed_xml_escapes_text_outside_cdata(self):
        comic_info = deepcopy(self.comic_info)
        comic_info.set("Comic Info", "Comic name", "Cats & Dogs")
        comic_info.set("Comic Info", "Author", "A < B")
        comic_info.set("RSS Feed", "Description", "Fish & Chips")
        comic_data = self.make_comic_data(_title="One < Two & Three")

        _, output, _ = self.build_feed_output(comic_data_dicts=[comic_data], comic_info=comic_info)
        root = self.parse_feed(output)
        channel = root.find("channel")
        item = channel.find("item")

        self.assertEqual("Cats & Dogs", channel.find("title").text)
        self.assertEqual("Fish & Chips", channel.find("description").text)
        self.assertEqual("A < B", channel.find("{http://purl.org/dc/elements/1.1/}creator").text)
        self.assertEqual("One < Two & Three", item.find("title").text)

    def test_build_rss_feed_invalid_post_date_raises_helpful_error(self):
        comic_data = self.make_comic_data(_post_date="1903-01-01")

        with self.assertRaises(ValueError) as cm:
            self.build_feed_output(comic_data_dicts=[comic_data])

        self.assertIn("Invalid post date '1903-01-01' for page 'Page 1'", str(cm.exception))
        self.assertIn("The date format is '%B %d, %Y'", str(cm.exception))

    def test_build_rss_feed_write_error_raises_helpful_error(self):
        feed_path = os.path.join("output", "feed.xml")

        with patch("builtins.open", side_effect=OSError("Permission denied")):
            with patch.dict(os.environ, {"OUTPUT_DIR": "output"}, clear=False):
                with self.assertRaises(ValueError) as cm:
                    build_rss_feed.build_rss_feed(self.comic_info, [self.make_comic_data()])

        self.assertIn(f"Could not write RSS feed to {feed_path}", str(cm.exception))
        self.assertIn("Verify the output directory exists and has write permissions.", str(cm.exception))
