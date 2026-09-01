import logging
import os
from collections import defaultdict
from configparser import RawConfigParser

from build.content.comic_data import page_to_template_context
from build.content.page_models import ComicPage
from build.content.site_config import get_pages_list, is_page_configured
from core import utils
from integrations.hooks import run_hook

logger = logging.getLogger(__name__)


def write_html_files(
        comic_folder: str,
        comic_info: RawConfigParser,
        pages: list[ComicPage],
        global_values: dict,
) -> None:
    tagged_pages_enabled = is_page_configured(comic_info, "tagged")
    if not tagged_pages_enabled and any(page.characters or page.tags for page in pages):
        comic_label = (
            f"Extra Comic '{comic_folder.strip('/')}'"
            if comic_folder
            else "Main comic"
        )
        logger.warning(
            "%s has published character or tag metadata, but no tagged page is configured. "
            "Built-in templates will display that metadata as plain text. Add a tagged page "
            "to [Pages] to generate character and tag archives.",
            comic_label,
        )
    template_folders = ["comic_git_engine/templates"]
    theme = comic_info.get("Comic Settings", "Theme", fallback="default")
    if theme:
        template_folders.insert(0, f"your_content/themes/{theme}/templates")
        if comic_folder:
            template_folders.insert(0, f"your_content/themes/{theme}/templates/{comic_folder}")
    logger.debug("Template folders: %s", template_folders)
    utils.build_jinja_environment(comic_info, template_folders)
    utils.build_markdown_parser(comic_info)
    logger.info("Writing %s comic pages", len(pages))
    for page in pages:
        html_path = f"{comic_folder}comic/{page.page_name}/index.html"
        context = page_to_template_context(page)
        context.update(global_values)
        context["tagged_pages_enabled"] = tagged_pages_enabled
        context["social_media"] = utils.get_social_media_data(
            comic_info,
            context,
            "comic",
            html_path,
            custom_social_media_data=page.social_media_source or None,
        )
        utils.write_to_template("comic", html_path, context)
    write_other_pages(comic_folder, comic_info, pages, global_values)
    run_hook(global_values["theme"], "build_other_pages", [comic_folder, comic_info, pages])


def write_other_pages(
        comic_folder: str,
        comic_info: RawConfigParser,
        pages: list[ComicPage],
        global_values: dict,
) -> None:
    if not pages:
        logger.warning("You're publishing a website with no comic pages. Are you sure about that?")
        base_context = {"_title": "Index"}
    else:
        base_context = page_to_template_context(pages[-1])
    base_context.update(global_values)
    base_context["tagged_pages_enabled"] = is_page_configured(comic_info, "tagged")
    for page_config in get_pages_list(comic_info):
        if page_config["template_name"] == "tagged":
            write_tagged_pages(comic_info, pages, base_context)
            continue
        template_name = page_config["template_name"]
        if template_name.lower() in ("index", "404"):
            html_path = f"{template_name}.html"
        else:
            html_path = os.path.join(template_name, "index.html")
        if comic_folder:
            html_path = os.path.join(comic_folder, html_path)
        if template_name == "latest" and not pages:
            continue
        context = base_context.copy()
        if page_config["title"]:
            context["_title"] = page_config["title"]
        context["social_media"] = utils.get_social_media_data(
            comic_info,
            context,
            template_name,
            html_path,
        )
        utils.write_to_template(template_name, html_path, context)


def write_tagged_pages(
        comic_info: RawConfigParser,
        pages: list[ComicPage],
        global_values: dict,
) -> None:
    if not pages:
        return
    tags = defaultdict(list)
    for page in pages:
        for character in page.characters:
            tags[character].append(page)
        for tag in page.tags:
            tags[tag].append(page)
    for tag, tagged_pages in tags.items():
        context = global_values.copy()
        context.update({
            "_title": f"Posts tagged with {tag}",
            "tag": tag,
            "tagged_pages": tagged_pages,
        })
        filename = f"tagged/{tag}/index.html"
        context["social_media"] = utils.get_social_media_data(
            comic_info,
            context,
            "tagged",
            filename,
        )
        try:
            utils.write_to_template("tagged", filename, context)
        except Exception:
            logger.exception("Failed to create '%s' from 'tagged' template", filename)
