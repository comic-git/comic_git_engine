import os
from configparser import RawConfigParser
from dataclasses import dataclass
from re import sub
from string import Formatter
from time import strptime, strftime
from typing import Any
from urllib.parse import urljoin
from xml.dom import minidom
from xml.etree import ElementTree
from xml.etree.ElementTree import register_namespace

from models import ComicBuildResult
from utils import get_comic_url

DEFAULT_RSS_LANGUAGE = "en-us"
DEFAULT_RSS_IMAGE = "your_content/images/banner.png"
DEFAULT_RSS_IMAGE_WIDTH = "100"
DEFAULT_RSS_IMAGE_HEIGHT = "36"


@dataclass(slots=True)
class FeedJob:
    comic_info: RawConfigParser
    comic_data_dicts: list[dict[str, Any]]
    feed_relative_path: str = "feed.xml"
    comic_page_relative_path: str = "comic"
    build_enabled: bool = True


def add_base_tags_to_channel(channel: ElementTree.Element, feed_context: dict[str, Any]) -> None:
    atom_link = ElementTree.SubElement(channel, "{http://www.w3.org/2005/Atom}link")
    atom_link.set("href", feed_context["feed_self_url"])
    atom_link.set("rel", "self")
    atom_link.set("type", "application/rss+xml")

    ElementTree.SubElement(channel, "title").text = feed_context["channel_title"]
    ElementTree.SubElement(channel, "description").text = feed_context["channel_description"]
    ElementTree.SubElement(channel, "link").text = feed_context["comic_url"]
    ElementTree.SubElement(channel, "{http://purl.org/dc/elements/1.1/}creator").text = feed_context["channel_author"]
    ElementTree.SubElement(channel, "language").text = feed_context["channel_language"]


def add_image_tag(channel: ElementTree.Element, feed_context: dict[str, Any]) -> None:
    image_tag = ElementTree.SubElement(channel, "image")
    ElementTree.SubElement(image_tag, "title").text = feed_context["channel_title"]
    ElementTree.SubElement(image_tag, "link").text = feed_context["comic_url"]
    ElementTree.SubElement(image_tag, "url").text = feed_context["channel_image_url"]
    ElementTree.SubElement(image_tag, "width").text = feed_context["channel_image_width"]
    ElementTree.SubElement(image_tag, "height").text = feed_context["channel_image_height"]


def build_item_link(comic_url: str, comic_page_relative_path: str, page_name: str) -> str:
    comic_page_relative_path = comic_page_relative_path.strip("/")
    return urljoin(comic_url, f"{comic_page_relative_path}/{page_name}/")


def format_guid(direct_link: str) -> str:
    return direct_link.lower().replace(" ", "_").replace("&", "_")


def parse_item_pub_date(comic_data: dict[str, Any], comic_info: RawConfigParser) -> str:
    date_format = comic_info.get("Comic Settings", "Date format")
    try:
        post_date = strptime(comic_data["_post_date"], date_format)
    except ValueError as e:
        raise ValueError(
            f"Invalid post date '{comic_data['_post_date']}' for page '{comic_data['page_name']}'\n"
            f"The date format is '{date_format}'. Ensure the date matches this format."
        ) from e
    return strftime("%a, %d %b %Y %H:%M:%S +0000", post_date)


def build_rss_post(comic_url: str, comic_paths: list[str], alt_text: str | None, post_html: str) -> str:
    comic_images = []
    for comic_path in comic_paths:
        comic_images.append(
            '<p><img src="{}"{}></p>'.format(
                urljoin(comic_url, comic_path),
                ' alt_text="{}"'.format(alt_text.replace(r'"', r'\"')) if alt_text else ""
            )
        )
    return "\n".join(comic_images) + "\n\n<hr>\n\n{}".format(post_html)


def pretty_xml(element: ElementTree.Element) -> str:
    raw_string = ElementTree.tostring(
        element, xml_declaration=True, encoding='utf-8', method="xml"
    ).decode("utf-8")
    flattened_string = sub(r"\n\s*", "", raw_string)
    return minidom.parseString(flattened_string).toprettyxml(indent="    ")


def validate_comic_data_dicts(comic_data_dicts: list[dict[str, Any]]) -> None:
    seen_page_names = set()
    for comic_data in comic_data_dicts:
        page_name = comic_data["page_name"]
        if page_name in seen_page_names:
            raise ValueError(
                f"Duplicate page_name '{page_name}' found in RSS feed input.\n"
                f"Each comic page in a single feed must have a unique page_name."
            )
        seen_page_names.add(page_name)


def order_comic_data_dicts(
        comic_info: RawConfigParser,
        comic_data_dicts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    ordered_comic_data_dicts = list(comic_data_dicts)
    if comic_info.getboolean("RSS Feed", "Newest first", fallback=False):
        ordered_comic_data_dicts.reverse()
    return ordered_comic_data_dicts


def normalize_item_categories(comic_data: dict[str, Any]) -> list[dict[str, str]]:
    categories = []
    if "_storyline" in comic_data:
        categories.append({"type": "storyline", "text": comic_data["_storyline"]})
    if "_characters" in comic_data:
        categories.extend({"type": "character", "text": character} for character in comic_data["_characters"])
    if "_tags" in comic_data:
        categories.extend({"type": "tag", "text": tag} for tag in comic_data["_tags"])
    return categories


def get_item_comic_page_relative_path(comic_data: dict[str, Any], default_comic_page_relative_path: str) -> str:
    return comic_data.get("rss_comic_page_relative_path", default_comic_page_relative_path)


def normalize_feed_item(
        comic_data: dict[str, Any],
        comic_info: RawConfigParser,
        comic_url: str,
        comic_page_relative_path: str,
        item_index: int,
) -> dict[str, Any]:
    direct_link = build_item_link(
        comic_url,
        get_item_comic_page_relative_path(comic_data, comic_page_relative_path),
        comic_data["page_name"],
    )
    return {
        "title": comic_data["_title"],
        "author": comic_info.get("Comic Info", "Author"),
        "pub_date": parse_item_pub_date(comic_data, comic_info),
        "link": direct_link,
        "guid": format_guid(direct_link),
        "categories": normalize_item_categories(comic_data),
        "description_placeholder_key": f"rss_cdata_{item_index}",
        "description_html": build_rss_post(
            comic_url,
            comic_data["comic_paths"],
            comic_data.get("escaped_alt_text"),
            comic_data["post_html"],
        ),
    }


def normalize_channel_context(
        comic_info: RawConfigParser,
        comic_url: str,
        feed_relative_path: str,
) -> dict[str, Any]:
    return {
        "comic_url": comic_url,
        "feed_relative_path": feed_relative_path,
        "feed_output_path": os.path.join(os.getenv("OUTPUT_DIR", ""), feed_relative_path),
        "feed_self_url": urljoin(comic_url, feed_relative_path),
        "channel_title": comic_info.get("Comic Info", "Comic name"),
        "channel_description": comic_info.get(
            "RSS Feed",
            "Description",
            fallback=comic_info.get("Comic Info", "Description"),
        ),
        "channel_author": comic_info.get("Comic Info", "Author"),
        "channel_language": comic_info.get("RSS Feed", "Language", fallback=DEFAULT_RSS_LANGUAGE),
        "channel_image_url": urljoin(
            comic_url,
            comic_info.get("RSS Feed", "Image", fallback=DEFAULT_RSS_IMAGE),
        ),
        "channel_image_width": comic_info.get("RSS Feed", "Image width", fallback=DEFAULT_RSS_IMAGE_WIDTH),
        "channel_image_height": comic_info.get("RSS Feed", "Image height", fallback=DEFAULT_RSS_IMAGE_HEIGHT),
    }


def build_feed_context(
        comic_info: RawConfigParser,
        comic_data_dicts: list[dict[str, Any]],
        feed_relative_path: str = "feed.xml",
        comic_page_relative_path: str = "comic",
) -> dict[str, Any]:
    comic_url, _ = get_comic_url(comic_info)
    if not comic_url.endswith("/"):
        comic_url += "/"

    ordered_comic_data_dicts = order_comic_data_dicts(comic_info, comic_data_dicts)
    feed_context = normalize_channel_context(comic_info, comic_url, feed_relative_path)
    feed_context["items"] = [
        normalize_feed_item(comic_data, comic_info, comic_url, comic_page_relative_path, item_index)
        for item_index, comic_data in enumerate(ordered_comic_data_dicts)
    ]
    return feed_context


def add_item(
        channel: ElementTree.Element,
        item_context: dict[str, Any],
        cdata_map: dict[str, str],
) -> None:
    item = ElementTree.SubElement(channel, "item")
    ElementTree.SubElement(item, "title").text = item_context["title"]
    ElementTree.SubElement(item, "{http://purl.org/dc/elements/1.1/}creator").text = item_context["author"]
    ElementTree.SubElement(item, "pubDate").text = item_context["pub_date"]
    ElementTree.SubElement(item, "link").text = item_context["link"]
    ElementTree.SubElement(item, "guid", isPermaLink="true").text = item_context["guid"]
    for category in item_context["categories"]:
        category_element = ElementTree.SubElement(item, "category")
        category_element.attrib["type"] = category["type"]
        category_element.text = category["text"]
    placeholder_key = item_context["description_placeholder_key"]
    cdata_map[placeholder_key] = "<![CDATA[{}]]>".format(item_context["description_html"])
    ElementTree.SubElement(item, "description").text = "{" + placeholder_key + "}"


def build_feed_xml(feed_context: dict[str, Any]) -> tuple[ElementTree.Element, dict[str, str]]:
    register_namespace("atom", "http://www.w3.org/2005/Atom")
    register_namespace("dc", "http://purl.org/dc/elements/1.1/")
    root = ElementTree.Element("rss")
    root.set("version", "2.0")
    channel = ElementTree.SubElement(root, "channel")

    add_base_tags_to_channel(channel, feed_context)
    add_image_tag(channel, feed_context)

    cdata_map = {}
    for item_context in feed_context["items"]:
        add_item(channel, item_context, cdata_map)
    return root, cdata_map


def serialize_feed_xml(root: ElementTree.Element, cdata_map: dict[str, str]) -> str:
    pretty_string = pretty_xml(root)
    return pretty_string.format(**cdata_map)


def write_feed_xml(feed_output_path: str, xml_text: str) -> None:
    try:
        with open(feed_output_path, 'wb') as f:
            f.write(bytes(xml_text, "utf-8"))
    except (OSError, IOError) as e:
        raise ValueError(
            f"Could not write RSS feed to {feed_output_path}\n"
            f"Verify the output directory exists and has write permissions."
        ) from e
    except UnicodeEncodeError as e:
        raise ValueError(
            f"Error encoding RSS feed to UTF-8\n"
            f"PLACEHOLDER: The feed may contain unsupported characters."
        ) from e


def build_feed_job(
        comic_info: RawConfigParser,
        comic_data_dicts: list[dict[str, Any]],
        feed_relative_path: str = "feed.xml",
        comic_page_relative_path: str = "comic",
        build_enabled: bool | None = None,
) -> FeedJob:
    if build_enabled is None:
        build_enabled = comic_info.getboolean("RSS Feed", "Build RSS feed", fallback=False)
    return FeedJob(
        comic_info=comic_info,
        comic_data_dicts=comic_data_dicts,
        feed_relative_path=feed_relative_path,
        comic_page_relative_path=comic_page_relative_path,
        build_enabled=build_enabled,
    )


def build_rss_feed_from_job(feed_job: FeedJob) -> None:
    if not feed_job.build_enabled:
        return

    validate_comic_data_dicts(feed_job.comic_data_dicts)
    feed_context = build_feed_context(
        feed_job.comic_info,
        feed_job.comic_data_dicts,
        feed_relative_path=feed_job.feed_relative_path,
        comic_page_relative_path=feed_job.comic_page_relative_path,
    )
    root, cdata_map = build_feed_xml(feed_context)
    xml_text = serialize_feed_xml(root, cdata_map)
    write_feed_xml(feed_context["feed_output_path"], xml_text)


def build_rss_feed(
        comic_info: RawConfigParser,
        comic_data_dicts: list[dict[str, Any]],
        feed_relative_path: str = "feed.xml",
        comic_page_relative_path: str = "comic",
) -> None:
    feed_job = build_feed_job(
        comic_info,
        comic_data_dicts,
        feed_relative_path=feed_relative_path,
        comic_page_relative_path=comic_page_relative_path,
    )
    build_rss_feed_from_job(feed_job)


def normalize_comic_folder(comic_folder: str) -> str:
    return comic_folder.strip("/")


def get_feed_relative_path(comic_folder: str) -> str:
    comic_folder = normalize_comic_folder(comic_folder)
    if not comic_folder:
        return "feed.xml"
    return f"{comic_folder}/feed.xml"


def get_comic_page_relative_path(comic_folder: str) -> str:
    comic_folder = normalize_comic_folder(comic_folder)
    if not comic_folder:
        return "comic"
    return f"{comic_folder}/comic"


def build_rss_feed_job_for_comic_result(comic_result: ComicBuildResult) -> FeedJob:
    return build_feed_job(
        comic_result.comic_info,
        build_rss_feed_comic_data_dicts_for_comic_result(comic_result),
        feed_relative_path=get_feed_relative_path(comic_result.comic_folder),
        comic_page_relative_path=get_comic_page_relative_path(comic_result.comic_folder),
    )


def get_main_comic_result(comic_results: list[ComicBuildResult]) -> ComicBuildResult:
    for comic_result in comic_results:
        if normalize_comic_folder(comic_result.comic_folder) == "":
            return comic_result
    raise ValueError("Could not find the main comic result for RSS generation.")


def is_rss_feed_enabled(comic_info: RawConfigParser) -> bool:
    return comic_info.getboolean("RSS Feed", "Build RSS feed", fallback=False)


def get_extra_comic_results(comic_results: list[ComicBuildResult]) -> list[ComicBuildResult]:
    return [
        comic_result
        for comic_result in comic_results
        if normalize_comic_folder(comic_result.comic_folder)
    ]


def should_combine_with_main_rss_feed(comic_result: ComicBuildResult) -> bool:
    if not normalize_comic_folder(comic_result.comic_folder):
        return False
    return comic_result.comic_info.getboolean("RSS Feed", "Combine with Main RSS Feed", fallback=False)


def get_rss_feed_item_title(
        comic_result: ComicBuildResult,
        comic_data: dict[str, Any],
) -> str:
    page_title = comic_data.get("page_title") or comic_data.get("_title") or comic_data["page_name"]
    title_format = comic_result.comic_info.get("RSS Feed", "RSS title format", fallback="").strip()
    if not title_format:
        return comic_data.get("_title", page_title)
    variables = {
        "comic_title": comic_result.comic_info.get("Comic Info", "Comic name", fallback=""),
        "page_title": page_title,
    }
    for _, field_name, _, _ in Formatter().parse(title_format):
        if field_name and field_name not in variables:
            raise ValueError(
                f"Unknown RSS title format variable '{field_name}'. "
                f"Supported variables: comic_title, page_title"
            )
    return title_format.format(**variables)


def build_rss_feed_comic_data_dicts_for_comic_result(
        comic_result: ComicBuildResult,
) -> list[dict[str, Any]]:
    rss_comic_data_dicts = []
    for comic_data in comic_result.comic_data_dicts:
        merged_comic_data = comic_data.copy()
        merged_comic_data["_title"] = get_rss_feed_item_title(comic_result, merged_comic_data)
        rss_comic_data_dicts.append(merged_comic_data)
    return rss_comic_data_dicts


def build_main_rss_comic_data_dicts(
        main_comic_result: ComicBuildResult,
        extra_comic_results: list[ComicBuildResult],
) -> list[dict[str, Any]]:
    main_rss_comic_data_dicts = build_rss_feed_comic_data_dicts_for_comic_result(main_comic_result)
    for comic_result in extra_comic_results:
        comic_page_relative_path = get_comic_page_relative_path(comic_result.comic_folder)
        for comic_data in build_rss_feed_comic_data_dicts_for_comic_result(comic_result):
            merged_comic_data = comic_data.copy()
            merged_comic_data["rss_comic_page_relative_path"] = comic_page_relative_path
            main_rss_comic_data_dicts.append(merged_comic_data)
    return main_rss_comic_data_dicts


def build_main_rss_feed_job(
        main_comic_result: ComicBuildResult,
        extra_comic_results: list[ComicBuildResult],
) -> FeedJob:
    return build_feed_job(
        main_comic_result.comic_info,
        build_main_rss_comic_data_dicts(main_comic_result, extra_comic_results),
        feed_relative_path="feed.xml",
        comic_page_relative_path="comic",
        build_enabled=is_rss_feed_enabled(main_comic_result.comic_info),
    )


def get_rss_feed_jobs(comic_results: list[ComicBuildResult]) -> list[FeedJob]:
    main_comic_result = get_main_comic_result(comic_results)
    extra_comic_results_to_combine = []
    extra_comic_results_with_independent_feeds = []
    for comic_result in get_extra_comic_results(comic_results):
        if not is_rss_feed_enabled(comic_result.comic_info):
            continue
        if should_combine_with_main_rss_feed(comic_result):
            extra_comic_results_to_combine.append(comic_result)
        else:
            extra_comic_results_with_independent_feeds.append(comic_result)

    feed_jobs = []
    if is_rss_feed_enabled(main_comic_result.comic_info):
        feed_jobs.append(
            build_main_rss_feed_job(
                main_comic_result,
                extra_comic_results_to_combine,
            )
        )
    feed_jobs.extend([
        build_rss_feed_job_for_comic_result(comic_result)
        for comic_result in extra_comic_results_with_independent_feeds
    ])
    return feed_jobs
