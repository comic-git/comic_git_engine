import logging
import os
import re
from configparser import RawConfigParser
from datetime import date
from time import strftime

from markdown2 import Markdown

from build.content.page_models import ComicPage
from integrations.hooks import run_hook

logger = logging.getLogger(__name__)
MARKDOWN = Markdown(extras=["strike", "break-on-newline", "markdown-in-html"])


def format_user_variable(key: str) -> str:
    key = re.sub(r"[^a-z0-9_]+", "_", key.lower()).strip("_")
    if key != "page_name":
        key = "_" + key
    return key


def get_ids(comic_list: list[ComicPage], index: int) -> dict[str, str]:
    return {
        "first_id": comic_list[0].page_name,
        "previous_id": comic_list[max(0, index - 1)].page_name,
        "current_id": comic_list[index].page_name,
        "next_id": comic_list[min(len(comic_list) - 1, index + 1)].page_name,
        "last_id": comic_list[-1].page_name,
    }


def enrich_comic_page(
        comic_folder: str,
        comic_info: RawConfigParser,
        page: ComicPage,
        first_id: str,
        previous_id: str,
        current_id: str,
        next_id: str,
        last_id: str,
) -> ComicPage:
    logger.info("[%s] Building page %s", strftime("%Y-%m-%d %H:%M:%S"), page.page_name)
    page.first_id = first_id
    page.previous_id = previous_id
    page.next_id = next_id
    page.last_id = last_id

    archive_date_format = comic_info.get("Archive", "Date format", fallback="")
    if archive_date_format:
        page.archive_post_date = date.fromisoformat(page.post_date).strftime(archive_date_format)
    else:
        page.archive_post_date = page.display_post_date

    post_parts = []
    for path in (
        f"your_content/{comic_folder}before post text.txt",
        f"your_content/{comic_folder}before post text.html",
    ):
        text = read_optional_utf8(path)
        if text is not None:
            post_parts.append(text)
    if page.post_md:
        post_parts.append(page.post_md)
    for path in (
        f"your_content/{comic_folder}after post text.txt",
        f"your_content/{comic_folder}after post text.html",
    ):
        text = read_optional_utf8(path)
        if text is not None:
            post_parts.append(text)
    page.post_md = "\n\n".join(post_parts)
    page.post_html = MARKDOWN.convert(page.post_md)

    theme = comic_info.get("Comic Settings", "Theme", fallback="default")
    hook_result = run_hook(
        theme,
        "extra_comic_dict_processing",
        [comic_folder, comic_info, page],
    )
    return hook_result if hook_result is not None else page


def read_optional_utf8(path: str) -> str | None:
    if not os.path.isfile(path):
        return None
    with open(path, "rb") as f:
        return f.read().decode("utf-8")


def build_comic_pages(
        comic_folder: str,
        comic_info: RawConfigParser,
        pages: list[ComicPage],
) -> list[ComicPage]:
    return [
        enrich_comic_page(comic_folder, comic_info, page, **get_ids(pages, index))
        for index, page in enumerate(pages)
    ]


def page_to_template_context(page: ComicPage) -> dict:
    context = {
        "page": page,
        "images": page.images,
        "page_name": page.page_name,
        "page_title": page.title,
        "page_dir": page.page_dir,
        "first_id": page.first_id,
        "previous_id": page.previous_id,
        "current_id": page.page_name,
        "next_id": page.next_id,
        "last_id": page.last_id,
        "archive_post_date": page.archive_post_date,
        "post_md": page.post_md,
        "post_html": page.post_html,
        "transcripts": page.transcripts,
        "_title": page.title,
        "_post_date": page.display_post_date,
        "_storyline": page.storyline,
        "_characters": page.characters,
        "_tags": page.tags,
        "_on_comic_click": page.on_comic_click,
    }
    context.update({format_user_variable(key): value for key, value in page.extra.items()})
    return context
