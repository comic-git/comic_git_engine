import hashlib
import logging
import os
from configparser import RawConfigParser

from PIL import Image

from build.content.page_models import ArchiveEntryMode, ComicImage, ComicPage, normalize_web_path
from build.content.site_config import get_archive_entry_mode

logger = logging.getLogger(__name__)


def resize(im: Image.Image, size: str) -> Image.Image:
    image_width, image_height = im.size
    size = size.strip()
    if "," in size:
        w, h = size.split(",")
        w, h = w.strip(), h.strip()
    elif size.endswith("%"):
        scale = float(size.strip("%")) / 100
        w, h = image_width * scale, image_height * scale
    elif size.endswith("h"):
        h = int(size[:-1].strip())
        w = image_width / image_height * h
    elif size.endswith("w"):
        w = int(size[:-1].strip())
        h = image_height / image_width * w
    else:
        raise ValueError(
            "Unknown resize value: {!r}\n"
            "Use format like '100,200' (width,height), '50%' (percentage), '100h' (height), or '100w' (width)."
            .format(size)
        )
    return im.resize((int(w), int(h)))


def save_image(im, path: str) -> None:
    try:
        if path.lower().endswith(("jpg", "jpeg")) and im.mode != "RGB":
            im = im.convert("RGB")
        im.save(path)
    except OSError as e:
        if str(e) == "cannot write mode RGBA as JPEG":
            bg = Image.new("RGB", im.size, "WHITE")
            bg.paste(im, (0, 0), im)
            bg.save(path)
        else:
            raise


def create_comic_thumbnail(
        comic_info: RawConfigParser,
        comic_image_path: str,
        thumbnail_path: str,
) -> None:
    overwrite = comic_info.getboolean(
        "Image Reprocessing",
        "Overwrite existing images",
        fallback=False,
    )
    if os.path.isfile(thumbnail_path) and not overwrite:
        return
    logger.info("Creating thumbnail for %s", os.path.basename(comic_image_path))
    with open(comic_image_path, "rb") as f:
        im = Image.open(f)
        thumbnail = resize(
            im,
            comic_info.get("Image Reprocessing", "Thumbnail size", fallback="100w"),
        )
        save_image(thumbnail, thumbnail_path)


def process_comic_images(comic_info: RawConfigParser, pages: list[ComicPage]) -> None:
    create_thumbnails = comic_info.getboolean(
        "Image Reprocessing",
        "Create thumbnails",
        fallback=False,
    )
    generate_image_thumbnails = (
        create_thumbnails
        and get_archive_entry_mode(comic_info) == ArchiveEntryMode.IMAGES
        and comic_info.getboolean("Archive", "Use thumbnails", fallback=False)
    )
    for page in pages:
        resolve_page_thumbnail(comic_info, page, create_thumbnails)
        for index, image in enumerate(page.images):
            resolve_image_thumbnail(
                comic_info,
                page,
                image,
                index,
                generate_image_thumbnails,
            )


def resolve_page_thumbnail(
        comic_info: RawConfigParser,
        page: ComicPage,
        create_thumbnails: bool,
) -> None:
    if page.thumbnail_disabled or page.thumbnail_explicit:
        return
    target = normalize_web_path(page.page_dir + "_thumbnail.jpg")
    if page.images and create_thumbnails:
        create_comic_thumbnail(comic_info, page.images[0].source_path, target)
        page.thumbnail_path = target
    else:
        page.thumbnail_path = target if os.path.isfile(target) else None


def resolve_image_thumbnail(
        comic_info: RawConfigParser,
        page: ComicPage,
        image: ComicImage,
        index: int,
        generate_image_thumbnails: bool,
) -> None:
    if image.thumbnail_disabled or image.thumbnail_explicit:
        return
    if index == 0 and page.thumbnail_path is not None:
        image.thumbnail_path = page.thumbnail_path
        return
    target = normalize_web_path(
        page.page_dir + f"_thumbnail_{hashlib.sha256(image.id.encode('utf-8')).hexdigest()}.jpg"
    )
    if generate_image_thumbnails:
        create_comic_thumbnail(comic_info, image.source_path, target)
        image.thumbnail_path = target
    else:
        image.thumbnail_path = target if os.path.isfile(target) else None
