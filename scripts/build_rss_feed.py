import os
from configparser import RawConfigParser
from re import sub
from time import strptime, strftime
from typing import List, Dict
from urllib.parse import urljoin
from xml.dom import minidom
from xml.etree import ElementTree
from xml.etree.ElementTree import register_namespace

from utils import get_comic_url

cdata_dict = {}


def add_base_tags_to_channel(channel, comic_url, comic_info):
    atom_link = ElementTree.SubElement(channel, "{http://www.w3.org/2005/Atom}link")
    atom_link.set("href", urljoin(comic_url, "feed.xml"))
    atom_link.set("rel", "self")
    atom_link.set("type", "application/rss+xml")

    # Set title, description, creator, and language
    ElementTree.SubElement(channel, "title").text = comic_info.get("Comic Info", "Comic name")
    ElementTree.SubElement(channel, "description").text = comic_info.get("RSS Feed", "Description")
    ElementTree.SubElement(channel, "link").text = comic_url
    ElementTree.SubElement(channel, "{http://purl.org/dc/elements/1.1/}creator").text = \
        comic_info.get("Comic Info", "Author")
    ElementTree.SubElement(channel, "language").text = comic_info.get("RSS Feed", "Language")


def add_image_tag(channel, comic_url, comic_info):
    image_tag = ElementTree.SubElement(channel, "image")
    ElementTree.SubElement(image_tag, "title").text = comic_info.get("Comic Info", "Comic name")
    ElementTree.SubElement(image_tag, "link").text = comic_url
    ElementTree.SubElement(image_tag, "url").text = urljoin(comic_url, comic_info.get("RSS Feed", "Image"))
    ElementTree.SubElement(image_tag, "width").text = comic_info.get("RSS Feed", "Image width")
    ElementTree.SubElement(image_tag, "height").text = comic_info.get("RSS Feed", "Image height")


def add_item(xml_parent, comic_data, comic_url, comic_info):
    global cdata_dict
    item = ElementTree.SubElement(xml_parent, "item")
    ElementTree.SubElement(item, "title").text = comic_data["_title"]
    ElementTree.SubElement(item, "{http://purl.org/dc/elements/1.1/}creator").text = \
        comic_info.get("Comic Info", "Author")
    post_date = strptime(comic_data["_post_date"], comic_info.get("Comic Settings", "Date format"))
    ElementTree.SubElement(item, "pubDate").text = strftime("%a, %d %b %Y %H:%M:%S +0000", post_date)
    direct_link = urljoin(comic_url, "comic/{}/".format(comic_data["page_name"]))
    ElementTree.SubElement(item, "link").text = direct_link
    guid = direct_link.lower().replace(" ", "_").replace("&", "_")
    ElementTree.SubElement(item, "guid", isPermaLink="true").text = guid
    if "_storyline" in comic_data:
        e = ElementTree.SubElement(item, "category")
        e.attrib["type"] = "storyline"
        e.text = comic_data["_storyline"]
    if "_characters" in comic_data:
        for character in comic_data["_characters"]:
            e = ElementTree.SubElement(item, "category")
            e.attrib["type"] = "character"
            e.text = character
    if "_tags" in comic_data:
        for tag in comic_data["_tags"]:
            e = ElementTree.SubElement(item, "category")
            e.attrib["type"] = "tag"
            e.text = tag
    html = build_rss_post(comic_url, comic_data["comic_paths"], comic_data.get("escaped_alt_text"), comic_data["post_html"])
    post_id = comic_data["page_name"].lower().replace(" ", "_").replace("&", "_")
    cdata_dict["post_id_" + post_id] = "<![CDATA[{}]]>".format(html)
    ElementTree.SubElement(item, "description").text = "{post_id_" + post_id + "}"


def build_rss_post(comic_url: str, comic_paths: list[str], alt_text: str, post_html: str):
    comic_images = []
    for comic_path in comic_paths:
        comic_images.append(
            '<p><img src="{}"{}></p>'.format(
                urljoin(comic_url, comic_path),
                ' alt_text="{}"'.format(alt_text.replace(r'"', r'\"')) if alt_text else ""
            )
        )
    return "\n".join(comic_images) + "\n\n<hr>\n\n{}".format(post_html)


def pretty_xml(element):
    raw_string = ElementTree.tostring(
        element, xml_declaration=True, encoding='utf-8', method="xml"
    ).decode("utf-8")
    flattened_string = sub(r"\n\s*", "", raw_string)
    pretty_string = minidom.parseString(flattened_string).toprettyxml(indent="    ")
    return pretty_string


def build_rss_feed(comic_info: RawConfigParser, comic_data_dicts: List[Dict]):
    global cdata_dict

    if not comic_info.getboolean("RSS Feed", "Build RSS feed"):
        return

    register_namespace("atom", "http://www.w3.org/2005/Atom")
    register_namespace("dc", "http://purl.org/dc/elements/1.1/")
    root = ElementTree.Element("rss")
    root.set("version", "2.0")
    channel = ElementTree.SubElement(root, "channel")

    # Build comic URL
    comic_url, _ = get_comic_url(comic_info)
    if not comic_url.endswith("/"):
        # To work well with urljoin
        comic_url += "/"

    add_base_tags_to_channel(channel, comic_url, comic_info)
    add_image_tag(channel, comic_url, comic_info)

    if comic_info.getboolean("RSS Feed", "Newest first", fallback=False):
        comic_data_dicts.reverse()

    for comic_data in comic_data_dicts:
        add_item(channel, comic_data, comic_url, comic_info)

    pretty_string = pretty_xml(root)

    # Replace CDATA manually, because XML is stupid and I can't figure out how to insert raw text
    pretty_string = pretty_string.format(**cdata_dict)

    with open(os.path.join(os.getenv("OUTPUT_DIR", ""), "feed.xml"), 'wb') as f:
        f.write(bytes(pretty_string, "utf-8"))
