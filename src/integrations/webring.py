import json
import os
from configparser import RawConfigParser
from typing import Any
from urllib.error import HTTPError
from urllib.request import urlopen


def load_webring_data(comic_info: RawConfigParser, comic_url: str) -> dict[str, Any]:
    if not comic_info.getboolean("Webring", "Enable webring", fallback=False):
        return {"enable_webring": False}
    url = comic_info.get("Webring", "Endpoint")
    if not url:
        raise ValueError("The 'Endpoint' option in the [Webring] section must be defined when 'Enable webring' is enabled.")
    webring_id = comic_info.get("Webring", "Webring ID")
    if not webring_id:
        raise ValueError("The 'Webring ID' option in the [Webring] section must be defined when 'Enable webring' is enabled.")

    if url == "local":
        local_path = os.path.join("your_content", "webring.json")
        try:
            with open(local_path) as response:
                data = json.load(response)
        except OSError as e:
            raise ValueError(
                f"Couldn't load webring data from local file {local_path}\n"
                f"Check that {local_path} exists in the host repo and contains valid webring JSON."
            ) from e
    else:
        try:
            with urlopen(url) as response:
                data = json.load(response)
        except HTTPError as e:
            raise ValueError(
                f"Couldn't load webring data from {url}\n"
                f"Check that the endpoint URL is correct and accessible, and that the server is responding."
            ) from e
    if data["version"] != 1:
        raise ValueError(
            f"Unknown webring data version: {data['version']}\n"
            f"Please report this error to the comic_git developers on our Discord. https://discord.gg/zmdHGXB"
        )
    show_all_members = comic_info.getboolean("Webring", "Show all members", fallback=False)
    jinja_variables = {
        "enable_webring": True,
        "webring_label": data.get("label"),
        "webring_home": data.get("home"),
        "show_all_members": show_all_members,
    }
    members = data["members"]
    if show_all_members:
        jinja_variables["webring_members"] = []
        exclude_own_comic = comic_info.getboolean("Webring", "Exclude own comic from members", fallback=False)
        for m in members:
            if m["id"] == webring_id and exclude_own_comic:
                continue
            jinja_variables["webring_members"].append(m)
    else:
        for index, member in enumerate(members):
            if member["id"] == webring_id:
                break
        else:
            print(f"Webring members:\n{json.dumps(data, indent=4)}")
            raise ValueError(
                f"Couldn't find '{webring_id}' in the list of members.\n"
                f"Verify your Webring ID matches exactly with one of the IDs in the webring data (see logs above)."
            )
        jinja_variables["webring_prev"] = members[(index - 1) % len(members)]
        jinja_variables["webring_next"] = members[(index + 1) % len(members)]

    return jinja_variables
