import json
from configparser import RawConfigParser
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch, mock_open, call

from jinja2 import StrictUndefined

from build.content.page_models import ComicImage, ComicPage
from core import utils


MUT = "core.utils."


class TestBuildJinjaEnvironment(TestCase):

    def test_always_uses_strict_undefined_even_with_removed_legacy_option(self):
        comic_info = RawConfigParser()
        comic_info.add_section("Comic Settings")
        comic_info.set("Comic Settings", "Allow missing variables in templates", "True")

        utils.build_jinja_environment(comic_info, ["templates"])

        self.assertIs(StrictUndefined, utils.jinja_environment.undefined)


class TestGetComicUrl(TestCase):

    @patch(MUT + "os.environ", {"GITHUB_REPOSITORY": "cvilbrandt/tamberlane"})
    def test_get_comic_url_on_github(self):
        comic_info = RawConfigParser()
        comic_info.add_section("Comic Settings")
        # No domain or subdirectory set
        self.assertEqual(
            ("https://cvilbrandt.github.io/tamberlane", "/tamberlane"),
            utils.get_comic_url(comic_info)
        )
        # With https:// and empty subdirectory
        comic_info.set("Comic Settings", "Comic domain", "https://www.tamberlanecomic.com")
        comic_info.set("Comic Settings", "Comic subdirectory", "")
        self.assertEqual(
            ("https://www.tamberlanecomic.com", ""),
            utils.get_comic_url(comic_info)
        )
        # With https:// and nonempty subdirectory
        comic_info.set("Comic Settings", "Comic domain", "https://www.tamberlanecomic.com")
        comic_info.set("Comic Settings", "Comic subdirectory", "my_comic")
        self.assertEqual(
            ("https://www.tamberlanecomic.com/my_comic", "/my_comic"),
            utils.get_comic_url(comic_info)
        )
        # With http://
        comic_info.set("Comic Settings", "Comic domain", "http://www.tamberlanecomic.com")
        comic_info.set("Comic Settings", "Comic subdirectory", "")
        self.assertEqual(
            ("https://www.tamberlanecomic.com", ""),
            utils.get_comic_url(comic_info)
        )
        # With no http://
        comic_info.set("Comic Settings", "Comic domain", "tamberlanecomic.com")
        comic_info.set("Comic Settings", "Comic subdirectory", "")
        self.assertEqual(
            ("https://tamberlanecomic.com", ""),
            utils.get_comic_url(comic_info)
        )
        # With no http://, and don't force use https
        comic_info.set("Comic Settings", "Comic domain", "tamberlanecomic.com")
        comic_info.set("Comic Settings", "Comic subdirectory", "")
        comic_info.set("Comic Settings", "Use https when building comic URL", "False")
        self.assertEqual(
            ("https://tamberlanecomic.com", ""),
            utils.get_comic_url(comic_info)
        )
        # With no http://, and force use https
        comic_info.set("Comic Settings", "Comic domain", "tamberlanecomic.com")
        comic_info.set("Comic Settings", "Comic subdirectory", "")
        comic_info.set("Comic Settings", "Use https when building comic URL", "True")
        self.assertEqual(
            ("https://tamberlanecomic.com", ""),
            utils.get_comic_url(comic_info)
        )

    @patch(MUT + "os.environ", {"GITHUB_REPOSITORY": "cvilbrandt/tamberlane"})
    @patch(MUT + "os.path.isfile", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data="tamberlanecomic.com")
    def test_get_comic_url_with_cname(self, *m):
        comic_info = RawConfigParser()
        comic_info.add_section("Comic Settings")
        # No domain or subdirectory set
        self.assertEqual(
            ("https://tamberlanecomic.com", ""),
            utils.get_comic_url(comic_info)
        )
        # With https:// and empty subdirectory
        comic_info.set("Comic Settings", "Comic domain", "https://www.tamberlanecomic.com")
        comic_info.set("Comic Settings", "Comic subdirectory", "")
        self.assertEqual(
            ("https://www.tamberlanecomic.com", ""),
            utils.get_comic_url(comic_info)
        )

    @patch(MUT + "os.environ", {"GITHUB_REPOSITORY": "cvilbrandt/cvilbrandt.github.io"})
    def test_get_comic_url_on_github_special_repo_name(self):
        comic_info = RawConfigParser()
        comic_info.add_section("Comic Settings")
        # No domain or subdirectory set
        self.assertEqual(
            ("https://cvilbrandt.github.io", ""),
            utils.get_comic_url(comic_info)
        )
        # With https:// and empty subdirectory
        comic_info.set("Comic Settings", "Comic domain", "https://www.tamberlanecomic.com")
        comic_info.set("Comic Settings", "Comic subdirectory", "")
        self.assertEqual(
            ("https://www.tamberlanecomic.com", ""),
            utils.get_comic_url(comic_info)
        )

    @patch(MUT + "os.environ", {})
    def test_get_comic_url_local(self):
        comic_info = RawConfigParser()
        comic_info.add_section("Comic Settings")
        # No domain or subdirectory set
        with self.assertRaises(ValueError):
            utils.get_comic_url(comic_info)
        # With https:// and empty subdirectory
        comic_info.set("Comic Settings", "Comic domain", "https://www.tamberlanecomic.com")
        comic_info.set("Comic Settings", "Comic subdirectory", "")
        self.assertEqual(
            ("https://www.tamberlanecomic.com", ""),
            utils.get_comic_url(comic_info)
        )


class TestGetSocialMediaData(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.comic_info = RawConfigParser()
        cls.comic_info.add_section("Comic Info")
        cls.comic_info.set("Comic Info", "Comic name", "My Comic!!")
        cls.comic_info.set("Comic Info", "Description", "hey hey you you i don't like your comic")
        image = ComicImage(
            id="main/001/page.png",
            filename="page.png",
            source_path="page.png",
            web_path="your_content/comics/001/page.png",
            title="Page 1",
            alt_text="This is where your first comic page will go!",
            thumbnail_path="your_content/comics/001/_thumbnail.jpg",
        )
        page = ComicPage(
            id="main/001",
            comic_id="main",
            comic_folder="",
            page_name="001",
            page_dir="your_content/comics/001/",
            url="/comic/001/",
            title="Page 1",
            post_date="2020-01-01",
            display_post_date="January 1, 2020",
            archive_post_date="January 1, 2020",
            images=[image],
            thumbnail_path="your_content/comics/001/_thumbnail.jpg",
        )
        cls.comic_data_dict = {
            "page": page,
            "post_md": "If you'd like some ideas on what you can do next with comic_git...",
            "_title": "Page 1",
            "comic_url": "https://ryanvilbrandt.github.io/comic_git_dev",
            "comic_folder": "",
        }

    def setUp(self):
        utils.social_media_data_by_comic = {}

    def test_default_data(self):
        """Test that a template not defined in the default data uses the 'base' fallback."""
        expected = {
            "og:type": "website",
            "og:site_name": "My Comic!!",
            "og:title": "Page 1",
            "og:description": "hey hey you you i don't like your comic",
            "og:url": "https://ryanvilbrandt.github.io/comic_git_dev/infinite_scroll/",
            "og:image": "https://ryanvilbrandt.github.io/comic_git_dev/your_content/images/preview_image.png",
        }
        actual = utils.get_social_media_data(
            self.comic_info,
            self.comic_data_dict,
            "infinite_scroll",
            "infinite_scroll/index.html",
        )
        self.assertEqual(expected, actual)

    def test_default_data_comic(self):
        """Test that a 'comic' template uses the 'comic' default data."""
        expected = {
            "og:type": "article",
            "og:site_name": "My Comic!!",
            "og:title": "Page 1",
            "og:description": "If you&#x27;d like some ideas on what you can do next with comic_git...",
            "og:url": "https://ryanvilbrandt.github.io/comic_git_dev/comic/001/",
            "og:image": "https://ryanvilbrandt.github.io/comic_git_dev/your_content/comics/001/_thumbnail.jpg",
            "og:image:alt": "This is where your first comic page will go!",
        }
        actual = utils.get_social_media_data(
            self.comic_info,
            self.comic_data_dict,
            "comic",
            "comic/001/index.html",
        )
        self.assertEqual(expected, actual)

    def test_default_data_latest(self):
        """Test that a 'latest' template uses the 'comic' default data. This also tests using references."""
        expected = {
            "og:type": "article",
            "og:site_name": "My Comic!!",
            "og:title": "Page 1",
            "og:description": "If you&#x27;d like some ideas on what you can do next with comic_git...",
            "og:url": "https://ryanvilbrandt.github.io/comic_git_dev/comic/001/",
            "og:image": "https://ryanvilbrandt.github.io/comic_git_dev/your_content/comics/001/_thumbnail.jpg",
            "og:image:alt": "This is where your first comic page will go!",
        }
        actual = utils.get_social_media_data(
            self.comic_info,
            self.comic_data_dict,
            "latest",
            "comic/001/index.html",
        )
        self.assertEqual(expected, actual)

    def test_comic_without_page_thumbnail_uses_site_preview(self):
        comic_data_dict = deepcopy(self.comic_data_dict)
        comic_data_dict["page"].thumbnail_path = None

        actual = utils.get_social_media_data(
            self.comic_info,
            comic_data_dict,
            "comic",
            "comic/001/index.html",
        )

        self.assertEqual(
            "https://ryanvilbrandt.github.io/comic_git_dev/your_content/images/preview_image.png",
            actual["og:image"],
        )
        self.assertEqual("This is where your first comic page will go!", actual["og:image:alt"])

    def test_comic_without_images_uses_site_preview_and_blank_alt(self):
        comic_data_dict = deepcopy(self.comic_data_dict)
        comic_data_dict["page"].thumbnail_path = None
        comic_data_dict["page"].images = []

        actual = utils.get_social_media_data(
            self.comic_info,
            comic_data_dict,
            "comic",
            "comic/001/index.html",
        )

        self.assertEqual(
            "https://ryanvilbrandt.github.io/comic_git_dev/your_content/images/preview_image.png",
            actual["og:image"],
        )
        self.assertEqual("", actual["og:image:alt"])

    def test_comic_url_with_slash(self):
        """Test that a comic_url with a slash at the end is handled properly."""
        comic_data_dict = deepcopy(self.comic_data_dict)
        comic_data_dict["comic_url"] = "https://www.tamberlanecomic.com/"
        expected = {
            "og:type": "article",
            "og:site_name": "My Comic!!",
            "og:title": "Page 1",
            "og:description": "If you&#x27;d like some ideas on what you can do next with comic_git...",
            "og:url": "https://www.tamberlanecomic.com/comic/001/",
            "og:image": "https://www.tamberlanecomic.com/your_content/comics/001/_thumbnail.jpg",
            "og:image:alt": "This is where your first comic page will go!",
        }
        actual = utils.get_social_media_data(
            self.comic_info,
            comic_data_dict,
            "comic",
            "comic/001/index.html",
        )
        self.assertEqual(expected, actual)

    def test_html_in_post_text(self):
        """Test that HTML in the post text is escaped properly."""
        comic_data_dict = deepcopy(self.comic_data_dict)
        comic_data_dict["post_md"] = "This is a post with <blink>HTML</blink> in it!"
        expected = {
            "og:type": "article",
            "og:site_name": "My Comic!!",
            "og:title": "Page 1",
            "og:description": "This is a post with &lt;blink&gt;HTML&lt;/blink&gt; in it!",
            "og:url": "https://ryanvilbrandt.github.io/comic_git_dev/comic/001/",
            "og:image": "https://ryanvilbrandt.github.io/comic_git_dev/your_content/comics/001/_thumbnail.jpg",
            "og:image:alt": "This is where your first comic page will go!",
        }
        actual = utils.get_social_media_data(
            self.comic_info,
            comic_data_dict,
            "comic",
            "comic/001/index.html",
        )
        self.assertEqual(expected, actual)

    @patch(MUT + "os.path.isfile", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data='{"comic": {"og:type": "video", "og:site_name": "_title"}}')
    def test_read_from_file(self, open_mock, isfile_mock):
        """Test that it will use data in the social_media.json file if it's present."""
        expected = {
            "og:type": "video",
            "og:site_name": "Page 1",
        }
        actual = utils.get_social_media_data(
            self.comic_info,
            self.comic_data_dict,
            "comic",
            "comic/001/index.html",
        )
        self.assertEqual(expected, actual)
        isfile_mock.assert_called_once_with("your_content/social_media.json")
        open_mock.assert_called_once_with("your_content/social_media.json")

    @patch(MUT + "os.path.isfile", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data='{"comic": {"og:type": "video", "og:site_name": "_title"}}')
    def test_read_from_file_cached(self, open_mock, isfile_mock):
        """Tests that loaded social media info is cached and so files are only read from once."""
        # Call 1
        expected = {
            "og:type": "video",
            "og:site_name": "Page 1",
        }
        actual = utils.get_social_media_data(
            self.comic_info,
            self.comic_data_dict,
            "comic",
            "comic/001/index.html",
        )
        self.assertEqual(expected, actual)
        # Call 2
        comic_data_dict = deepcopy(self.comic_data_dict)
        comic_data_dict["_title"] = "Page 2"
        expected = {
            "og:type": "video",
            "og:site_name": "Page 2",
        }
        actual = utils.get_social_media_data(
            self.comic_info,
            comic_data_dict,
            "comic",
            "comic/002/index.html",
        )
        self.assertEqual(expected, actual)

        isfile_mock.assert_called_once_with("your_content/social_media.json")
        open_mock.assert_called_once_with("your_content/social_media.json")

    @patch(MUT + "os.path.isfile", return_value=False)
    @patch("builtins.open", new_callable=mock_open, read_data='{"comic": {"og:type": "video", "og:site_name": "_title"}}')
    def test_extra_comic_folders(self, open_mock, isfile_mock):
        """Test that extra comics can define their own social_media.json, and they will be cached differently than
           the main comic/each other."""
        # Main comic, no file
        expected = {
            "og:type": "article",
            "og:site_name": "My Comic!!",
            "og:title": "Page 1",
            "og:description": "If you&#x27;d like some ideas on what you can do next with comic_git...",
            "og:url": "https://ryanvilbrandt.github.io/comic_git_dev/comic/001/",
            "og:image": "https://ryanvilbrandt.github.io/comic_git_dev/your_content/comics/001/_thumbnail.jpg",
            "og:image:alt": "This is where your first comic page will go!",
        }
        actual = utils.get_social_media_data(
            self.comic_info,
            self.comic_data_dict,
            "comic",
            "comic/001/index.html",
        )
        self.assertEqual(expected, actual)
        # Extra Comic 1, yes file
        comic_data_dict = deepcopy(self.comic_data_dict)
        comic_data_dict["comic_folder"] = "extra_comic_1"
        comic_data_dict["_title"] = "Extra Comic Page 1"
        isfile_mock.return_value = True
        expected = {
            "og:type": "video",
            "og:site_name": "Extra Comic Page 1",
        }
        actual = utils.get_social_media_data(
            self.comic_info,
            comic_data_dict,
            "comic",
            "comic/001/index.html",
        )
        self.assertEqual(expected, actual)
        # Extra Comic 2, no file
        comic_data_dict = deepcopy(self.comic_data_dict)
        comic_data_dict["comic_folder"] = "extra_comic_2"
        comic_data_dict["_title"] = "Extra Comic Page 2"
        isfile_mock.return_value = False
        expected = {
            "og:type": "article",
            "og:site_name": "My Comic!!",
            "og:title": "Extra Comic Page 2",
            "og:description": "If you&#x27;d like some ideas on what you can do next with comic_git...",
            "og:url": "https://ryanvilbrandt.github.io/comic_git_dev/comic/002/",
            "og:image": "https://ryanvilbrandt.github.io/comic_git_dev/your_content/comics/001/_thumbnail.jpg",
            "og:image:alt": "This is where your first comic page will go!",
        }
        actual = utils.get_social_media_data(
            self.comic_info,
            comic_data_dict,
            "comic",
            "comic/002/index.html",
        )
        self.assertEqual(expected, actual)

        isfile_mock.assert_has_calls([
            call("your_content/social_media.json"),
            call(r"extra_comic_1\your_content/social_media.json"),
            call(r"extra_comic_2\your_content/social_media.json"),
            call("your_content/social_media.json"),
        ])
        open_mock.assert_called_once_with(r"extra_comic_1\your_content/social_media.json")

    @patch(MUT + "os.path.isfile", side_effect=lambda path: path == "your_content/social_media.json")
    @patch("builtins.open", new_callable=mock_open, read_data='{"comic": {"og:type": "video", "og:site_name": "_title"}}')
    def test_extra_comic_inherits_main_social_media_file(self, open_mock, isfile_mock):
        """Test that an Extra Comic falls back to the main comic social_media.json if it has no local file."""
        comic_data_dict = deepcopy(self.comic_data_dict)
        comic_data_dict["comic_folder"] = "extra_comic_2"
        comic_data_dict["_title"] = "Extra Comic Page 2"

        expected = {
            "og:type": "video",
            "og:site_name": "Extra Comic Page 2",
        }
        actual = utils.get_social_media_data(
            self.comic_info,
            comic_data_dict,
            "comic",
            "comic/002/index.html",
        )
        self.assertEqual(expected, actual)

        isfile_mock.assert_has_calls([
            call(r"extra_comic_2\your_content/social_media.json"),
            call("your_content/social_media.json"),
        ])
        open_mock.assert_called_once_with("your_content/social_media.json")

    @patch(MUT + "os.path.isfile", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({
        "base": {
            "og:type": "audio",
            "og:site_name": "My Comic!!",
        },
        "comic": {
            "_inherits": "base",
            "og:type": "video",
            "og:title": "Page 1",
        },
        "latest": {
            "_inherits": "comic",
            "og:type": "cellotype",
            "og:description": "That's a lot of nested data",
        },
    }))
    def test_inherits(self, *_mocks):
        """Tests that _inherits properly overlaps/overrides data as needed."""
        # latest
        expected = {
            "og:type": "cellotype",
            "og:site_name": "My Comic!!",
            "og:title": "Page 1",
            "og:description": "That's a lot of nested data",
        }
        actual = utils.get_social_media_data(
            self.comic_info,
            self.comic_data_dict,
            "latest",
            "comic/001/index.html",
        )
        self.assertEqual(expected, actual)

        # comic
        expected = {
            "og:type": "video",
            "og:site_name": "My Comic!!",
            "og:title": "Page 1",
        }
        actual = utils.get_social_media_data(
            self.comic_info,
            self.comic_data_dict,
            "comic",
            "comic/001/index.html",
        )
        self.assertEqual(expected, actual)

        # non-existent-template
        expected = {
            "og:type": "audio",
            "og:site_name": "My Comic!!",
        }
        actual = utils.get_social_media_data(
            self.comic_info,
            self.comic_data_dict,
            "non-existent-template",
            "comic/001/index.html",
        )
        self.assertEqual(expected, actual)
