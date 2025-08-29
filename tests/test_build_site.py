from configparser import RawConfigParser
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch

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
