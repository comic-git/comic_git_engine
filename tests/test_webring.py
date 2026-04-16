from configparser import RawConfigParser
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch

from integrations import webring


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


@patch("integrations.webring.json.load", return_value=WEBRING_JSON)
@patch("integrations.webring.urlopen")
class TestWebring(TestCase):
    def setUp(self):
        self.comic_info = RawConfigParser()
        self.comic_info.add_section("Webring")
        self.comic_info.set("Webring", "Enable webring", "True")
        self.comic_info.set("Webring", "Endpoint", "https://webring.example.com/api")
        self.comic_info.set("Webring", "Webring ID", "comic_b")

    def test_enable_webring_false(self, _mock_urlopen, _mock_json_load):
        self.comic_info.set("Webring", "Enable webring", "False")
        self.assertEqual(
            {"enable_webring": False},
            webring.load_webring_data(self.comic_info, COMIC_URL),
        )
        _mock_urlopen.assert_not_called()

    def test_undefined_endpoint(self, _mock_urlopen, _mock_json_load):
        self.comic_info.set("Webring", "Endpoint", "")
        msg = r"The 'Endpoint' option in the \[Webring\] section must be defined when 'Enable webring' is enabled."
        with self.assertRaisesRegex(ValueError, msg):
            webring.load_webring_data(self.comic_info, COMIC_URL)
        _mock_urlopen.assert_not_called()

    def test_invalid_version(self, _mock_urlopen, _mock_json_load):
        webring_json = deepcopy(WEBRING_JSON)
        webring_json["version"] = 10
        _mock_json_load.return_value = webring_json
        with self.assertRaisesRegex(ValueError, "Unknown webring data version: 10"):
            webring.load_webring_data(self.comic_info, COMIC_URL)

    def test_invalid_webring_id(self, _mock_urlopen, _mock_json_load):
        self.comic_info.set("Webring", "Webring ID", "")
        msg = r"The 'Webring ID' option in the \[Webring\] section must be defined when 'Enable webring' is enabled and 'Show all members' is False."
        with self.assertRaisesRegex(ValueError, msg):
            webring.load_webring_data(self.comic_info, COMIC_URL)

    def test_webring_id_not_found(self, _mock_urlopen, _mock_json_load):
        self.comic_info.set("Webring", "Webring ID", "not_a_real_id")
        msg = r"Couldn't find 'not_a_real_id' in the list of members.\s+Verify your Webring ID matches exactly with one of the IDs in the webring data \(see logs above\)\."
        with self.assertRaisesRegex(ValueError, msg):
            webring.load_webring_data(self.comic_info, COMIC_URL)

    def test_assert_urlopen(self, _mock_urlopen, _mock_json_load):
        self.assertEqual(
            {
                "enable_webring": True,
                "webring_label": None,
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
            webring.load_webring_data(self.comic_info, COMIC_URL),
        )
        _mock_urlopen.assert_called_once_with("https://webring.example.com/api")

    def test_relative_path(self, _mock_urlopen, _mock_json_load):
        self.comic_info.set("Webring", "Endpoint", "/your_content/webring.json")
        webring.load_webring_data(self.comic_info, COMIC_URL)
        _mock_urlopen.assert_called_once_with("https://ryanvilbrandt.github.io/comic_git_dev/your_content/webring.json")

    def test_first_member(self, _mock_urlopen, _mock_json_load):
        self.comic_info.set("Webring", "Webring ID", "comic_a")
        self.assertEqual("comic_c", webring.load_webring_data(self.comic_info, COMIC_URL)["webring_prev"]["id"])

    def test_last_member(self, _mock_urlopen, _mock_json_load):
        self.comic_info.set("Webring", "Webring ID", "comic_c")
        self.assertEqual("comic_a", webring.load_webring_data(self.comic_info, COMIC_URL)["webring_next"]["id"])

    def test_show_all_members(self, _mock_urlopen, _mock_json_load):
        self.comic_info.set("Webring", "Show all members", "True")
        data = webring.load_webring_data(self.comic_info, COMIC_URL)
        self.assertTrue(data["show_all_members"])
        self.assertEqual(3, len(data["webring_members"]))

    def test_show_all_members_can_exclude_own_comic(self, _mock_urlopen, _mock_json_load):
        self.comic_info.set("Webring", "Show all members", "True")
        self.comic_info.set("Webring", "Exclude own comic from members", "True")
        data = webring.load_webring_data(self.comic_info, COMIC_URL)
        self.assertEqual(["comic_a", "comic_c"], [member["id"] for member in data["webring_members"]])
