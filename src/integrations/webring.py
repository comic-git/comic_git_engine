"""External webring data and explicitly selected display trust."""
import json
import logging
from configparser import RawConfigParser
from http.client import HTTPException
from time import monotonic
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import urlopen

import nh3
from markdown2 import markdown
from markupsafe import Markup
from build.content.content_paths import WEBRING_JSON

logger = logging.getLogger(__name__)
MAX_RESPONSE_BYTES = 1024 * 1024
FETCH_TIMEOUT = 10
FETCH_DEADLINE = 20
FETCH_ATTEMPTS = 2
# Labels sit inside links/headings: no nested links, blocks, images, or attributes.
INLINE_TAGS = {"em", "strong", "b", "i", "code", "s", "del", "br"}


def validate_url(value: str, field: str, *, optional: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Webring {field} must be a string")
    if optional and not value:
        return value
    if any(ord(c) < 33 or ord(c) == 127 for c in value) or "\\" in value:
        raise ValueError(f"Webring {field} must be an absolute HTTP(S) URL without whitespace")
    parsed = urlsplit(value)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError(f"Webring {field} must be an absolute HTTP(S) URL without credentials")
    _ = parsed.port
    return value


def read_json(response, *, deadline: float | None = None) -> dict:
    chunks = []
    size = 0
    read = getattr(response, "read1", response.read)
    while True:
        if deadline is not None and monotonic() > deadline:
            raise TimeoutError("Webring response exceeded its time limit")
        chunk = read(min(65536, MAX_RESPONSE_BYTES + 1 - size))
        if not chunk:
            break
        size += len(chunk)
        if size > MAX_RESPONSE_BYTES:
            raise ValueError("Webring response exceeds 1 MiB")
        chunks.append(chunk)
    try:
        return json.loads(b"".join(chunks))
    except RecursionError as error:
        raise ValueError("Webring JSON is nested too deeply") from error


def fetch_data(url: str) -> dict:
    if url == "local":
        with open(WEBRING_JSON, "rb") as response:
            return read_json(response)
    validate_url(url, "Endpoint")
    for attempt in range(FETCH_ATTEMPTS):
        try:
            deadline = monotonic() + FETCH_DEADLINE
            with urlopen(url, timeout=FETCH_TIMEOUT) as response:
                validate_url(response.geturl(), "redirect URL")
                return read_json(response, deadline=deadline)
        except (OSError, URLError, HTTPException) as error:
            retryable = not isinstance(error, HTTPError) or error.code in {408, 429, 500, 502, 503, 504}
            if not retryable or attempt + 1 == FETCH_ATTEMPTS:
                raise
    raise RuntimeError("Unreachable webring fetch state")


def display_text(text: str, mode: str) -> str:
    if mode == "text":
        return text
    if mode == "unsafe_html":
        return Markup(text)
    return Markup(nh3.clean(markdown(text), tags=INLINE_TAGS, attributes={},
                            clean_content_tags={"script", "style"}, link_rel=None).strip())


def prepare_data(data: Any, mode: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("Webring response must be a JSON object")
    if type(data.get("version")) is not int or data["version"] != 1:
        raise ValueError(f"Unknown webring data version: {data.get('version')}")
    members = data.get("members")
    if not isinstance(members, list) or not members:
        raise ValueError("Webring members must be a non-empty list")

    def entry(value, field, member=False):
        if not isinstance(value, dict) or not isinstance(value.get("name", ""), str):
            raise ValueError(f"Webring {field}.name must be a string")
        result = dict(value)
        result["name"] = value.get("name", "")
        if member and (not isinstance(value.get("id"), str) or not value["id"]):
            raise ValueError(f"Webring {field}.id must be a non-empty string")
        result["url"] = validate_url(value.get("url"), f"{field}.url")
        result["image"] = validate_url(value.get("image", ""), f"{field}.image", optional=True)
        result["name_html"] = display_text(result["name"], mode)
        return result

    prepared = [entry(m, f"members[{i}]", True) for i, m in enumerate(members)]
    ids = [m["id"] for m in prepared]
    if len(set(ids)) != len(ids):
        raise ValueError("Webring member IDs must be unique")
    label = data.get("label")
    if label is not None and not isinstance(label, str):
        raise ValueError("Webring label must be a string")
    return {"members": prepared,
            "home": entry(data["home"], "home") if data.get("home") is not None else None,
            "label": display_text(label, mode) if label else label}


def load_webring_data(comic_info: RawConfigParser, comic_url: str) -> dict[str, Any]:
    if not comic_info.getboolean("Webring", "Enable webring", fallback=False):
        return {"enable_webring": False}
    # Configuration mistakes always fail, even with optional network/data omission.
    url = comic_info.get("Webring", "Endpoint", fallback="")
    if not url:
        raise ValueError("The 'Endpoint' option in the [Webring] section must be defined when 'Enable webring' is enabled.")
    if url != "local":
        validate_url(url, "Endpoint")
    webring_id = comic_info.get("Webring", "Webring ID", fallback="")
    if not webring_id:
        raise ValueError("The 'Webring ID' option in the [Webring] section must be defined when 'Enable webring' is enabled.")
    mode = comic_info.get("Webring", "Text mode", fallback="text")
    on_error = comic_info.get("Webring", "On error", fallback="abort")
    if mode not in {"text", "markdown", "unsafe_html"}:
        raise ValueError("Webring Text mode must be text, markdown, or unsafe_html")
    if on_error not in {"abort", "omit"}:
        raise ValueError("Webring On error must be abort or omit")
    show_all = comic_info.getboolean("Webring", "Show all members", fallback=False)
    exclude_own = comic_info.getboolean("Webring", "Exclude own comic from members", fallback=False)
    if mode == "unsafe_html":
        logger.warning("Webring unsafe_html is enabled: the JSON source can execute scripts on your website. Only use a trusted source.")
    try:
        data = prepare_data(fetch_data(url), mode)
        members = data["members"]
        result = {"enable_webring": True, "webring_label": data["label"],
                  "webring_home": data["home"], "show_all_members": show_all}
        if show_all:
            result["webring_members"] = [m for m in members if not (exclude_own and m["id"] == webring_id)]
        else:
            index = next((i for i, m in enumerate(members) if m["id"] == webring_id), None)
            if index is None:
                raise ValueError(f"Couldn't find '{webring_id}' in the list of members. Verify your Webring ID matches the endpoint.")
            result["webring_prev"] = members[(index - 1) % len(members)]
            result["webring_next"] = members[(index + 1) % len(members)]
        return result
    except (ValueError, OSError, URLError, HTTPException) as error:
        if on_error == "omit":
            logger.warning("Webring omitted from this build (On error = omit): %s", error)
            return {"enable_webring": False}
        raise ValueError(f"Couldn't load webring: {error}") from error
