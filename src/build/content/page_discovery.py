import logging
import os
import shutil
from datetime import datetime
from glob import iglob

from configparser import RawConfigParser
from pytz import timezone

from build.content.loaders import load_page_source
from build.content.page_models import (
    ComicImage,
    ComicPage,
    build_image_anchor_id,
    build_image_id,
    build_page_id,
    normalize_comic_id,
    normalize_web_path,
    resolve_image_alt_text,
    resolve_image_title,
    resolve_page_title,
    validate_page_asset_path,
    validate_unique_filenames,
)
from build.content.page_sources import PageSource, iso_date_to_legacy
from build.content.site_config import get_image_title_fallback
from build.content.transcripts import render_transcript_sources, sort_transcript_languages
from core import utils
from integrations.hooks import run_hook

logger = logging.getLogger(__name__)


def discover_pages(
        comic_folder: str,
        comic_info: RawConfigParser,
        delete_scheduled_posts: bool,
        publish_all_comics: bool,
) -> tuple[list[ComicPage], int]:
    try:
        tz_info = timezone(comic_info.get("Comic Settings", "Timezone"))
    except Exception as e:
        raise ValueError(
            f"Invalid timezone specified in [Comic Settings] Timezone: {e}\n"
            "Use a valid IANA timezone name (e.g., 'America/Los_Angeles', 'Europe/London', 'UTC'). "
            "See https://en.wikipedia.org/wiki/List_of_tz_database_time_zones for a complete list."
        ) from e

    local_time = datetime.now(tz=tz_info)
    logger.info("Local time is %s", local_time)
    pages = []
    scheduled_post_count = 0
    theme = comic_info.get("Comic Settings", "Theme", fallback="default")
    for page_path in iglob(f"your_content/{comic_folder}comics/*/"):
        page_path = normalize_web_path(page_path) + "/"
        filepath, page_source = load_page_source(page_path, comic_folder, comic_info)
        if page_source is None or filepath is None:
            logger.warning("%s is missing its info.ini/info.toml file. Skipping", page_path)
            continue
        try:
            post_date = tz_info.localize(datetime.fromisoformat(page_source.post_date))
        except ValueError as e:
            raise ValueError(
                f"Invalid post_date in {filepath}: {page_source.post_date}\n"
                "Expected an ISO YYYY-MM-DD date after source loading."
            ) from e
        if post_date > local_time and not publish_all_comics:
            scheduled_post_count += 1
            if delete_scheduled_posts:
                logger.warning("Deleting scheduled page %s", page_path)
                shutil.rmtree(page_path)
            continue

        page = build_discovered_page(comic_folder, comic_info, page_path, page_source)
        hook_result = run_hook(
            theme,
            "extra_page_info_processing",
            [comic_folder, comic_info, page_path, page],
        )
        if hook_result is not None:
            page = hook_result
        logger.debug("Page: %s", page)
        pages.append(page)

    pages.sort(key=lambda page: (page.post_date, page.page_name))
    return pages, scheduled_post_count


def build_discovered_page(
        comic_folder: str,
        comic_info: RawConfigParser,
        page_path: str,
        source: PageSource,
) -> ComicPage:
    page_name = os.path.basename(os.path.normpath(page_path))
    validate_unique_filenames([image.filename for image in source.images])
    fallback = get_image_title_fallback(comic_info)
    page_title = resolve_page_title(source.title, [image.filename for image in source.images], page_name)
    if source.title is not None and not source.title.strip():
        logger.warning("Page %s has a blank title; using fallback title %r", page_name, page_title)

    page_dir = f"your_content/{comic_folder}comics/{page_name}/"
    images = []
    resolved_source_paths = set()
    for image_source in source.images:
        filename, source_path = validate_page_asset_path(page_path, image_source.filename, "comic image")
        resolved_source_path = os.path.normcase(source_path)
        if resolved_source_path in resolved_source_paths:
            raise ValueError(f"Duplicate comic image declaration: {filename}")
        resolved_source_paths.add(resolved_source_path)
        image_id = build_image_id(comic_folder, page_name, filename)
        thumbnail_path, thumbnail_explicit, thumbnail_disabled = resolve_explicit_thumbnail(
            page_path,
            page_dir,
            image_source.thumbnail,
            f"thumbnail for image {filename}",
        )
        images.append(
            ComicImage(
                id=image_id,
                filename=filename,
                source_path=source_path,
                web_path=normalize_web_path(page_dir + filename),
                anchor_id=build_image_anchor_id(image_id),
                title=resolve_image_title(image_source.title, source.title, filename, fallback),
                alt_text=resolve_image_alt_text(image_source.alt_text, source.alt_text),
                thumbnail_path=thumbnail_path,
                thumbnail_explicit=thumbnail_explicit,
                thumbnail_disabled=thumbnail_disabled,
            )
        )

    thumbnail_path, thumbnail_explicit, thumbnail_disabled = resolve_explicit_thumbnail(
        page_path,
        page_dir,
        source.thumbnail,
        f"thumbnail for page {page_name}",
    )
    transcripts = {}
    if comic_info.getboolean("Transcripts", "Enable transcripts"):
        transcript_sources = sort_transcript_languages(source.transcripts, comic_info)
        transcripts = render_transcript_sources(transcript_sources)

    display_post_date = iso_date_to_legacy(
        source.post_date,
        comic_info.get("Comic Settings", "Date format"),
    )
    base_dir = utils.BASE_DIRECTORY.rstrip("/")
    page_url = f"{base_dir}/{comic_folder}comic/{page_name}/"
    return ComicPage(
        id=build_page_id(comic_folder, page_name),
        comic_id=normalize_comic_id(comic_folder),
        comic_folder=comic_folder,
        page_name=page_name,
        page_dir=page_dir,
        url=page_url,
        title=page_title,
        post_date=source.post_date,
        display_post_date=display_post_date,
        archive_post_date=display_post_date,
        images=images,
        thumbnail_path=thumbnail_path,
        thumbnail_explicit=thumbnail_explicit,
        thumbnail_disabled=thumbnail_disabled,
        storyline=source.storyline,
        characters=list(source.characters),
        tags=list(source.tags),
        transcript_languages=list(transcripts),
        post_md=source.post_text,
        transcripts=transcripts,
        social_media_source=dict(source.social_media),
        extra=dict(source.extra),
        on_comic_click=comic_info.get(
            "Comic Settings",
            "On comic click",
            fallback="Next comic",
        ).lower(),
    )


def resolve_explicit_thumbnail(
        page_path: str,
        page_dir: str,
        configured_thumbnail: str | None,
        description: str,
) -> tuple[str | None, bool, bool]:
    if configured_thumbnail is None:
        return None, False, False
    if configured_thumbnail == "":
        return None, False, True
    filename, _source_path = validate_page_asset_path(page_path, configured_thumbnail, description)
    return normalize_web_path(page_dir + filename), True, False
