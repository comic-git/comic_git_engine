import os
from configparser import RawConfigParser
from re import sub
from time import strptime, strftime
from typing import Any
from urllib.parse import urljoin
from xml.dom import minidom
from xml.etree import ElementTree
from xml.etree.ElementTree import register_namespace

from utils import get_comic_url


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


def normalize_feed_item(
        comic_data: dict[str, Any],
        comic_info: RawConfigParser,
        comic_url: str,
        comic_page_relative_path: str,
        item_index: int,
) -> dict[str, Any]:
    direct_link = build_item_link(comic_url, comic_page_relative_path, comic_data["page_name"])
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
        "channel_description": comic_info.get("RSS Feed", "Description"),
        "channel_author": comic_info.get("Comic Info", "Author"),
        "channel_language": comic_info.get("RSS Feed", "Language"),
        "channel_image_url": urljoin(comic_url, comic_info.get("RSS Feed", "Image")),
        "channel_image_width": comic_info.get("RSS Feed", "Image width"),
        "channel_image_height": comic_info.get("RSS Feed", "Image height"),
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


def build_rss_feed(
        comic_info: RawConfigParser,
        comic_data_dicts: list[dict[str, Any]],
        feed_relative_path: str = "feed.xml",
        comic_page_relative_path: str = "comic",
) -> None:
    if not comic_info.getboolean("RSS Feed", "Build RSS feed"):
        return

    validate_comic_data_dicts(comic_data_dicts)
    feed_context = build_feed_context(
        comic_info,
        comic_data_dicts,
        feed_relative_path=feed_relative_path,
        comic_page_relative_path=comic_page_relative_path,
    )
    root, cdata_map = build_feed_xml(feed_context)
    xml_text = serialize_feed_xml(root, cdata_map)
    write_feed_xml(feed_context["feed_output_path"], xml_text)
