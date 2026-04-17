import os
from configparser import RawConfigParser
from typing import Dict, List

from PIL import Image


def resize(im: Image, size: str) -> Image:
    image_width, image_height = im.size
    if "," in size:
        w, h = size.strip().split(",")
        w, h = w.strip(), h.strip()
    elif size.endswith("%"):
        size = float(size.strip().strip("%"))
        size = size / 100
        w, h = image_width * size, image_height * size
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


def save_image(im, path):
    try:
        if path.lower().endswith("jpg") or path.lower().endswith("jpeg"):
            if im.mode != 'RGB':
                im = im.convert('RGB')
        im.save(path)
    except OSError as e:
        if str(e) == "cannot write mode RGBA as JPEG":
            bg = Image.new("RGB", im.size, "WHITE")
            bg.paste(im, (0, 0), im)
            bg.save(path)
        else:
            raise


def create_comic_thumbnail(comic_info, comic_page_path):
    section = "Image Reprocessing"
    comic_page_dir = os.path.dirname(comic_page_path)
    comic_page_name, _comic_page_ext = os.path.splitext(os.path.basename(comic_page_path))
    with open(comic_page_path, "rb") as f:
        im = Image.open(f)
        thumbnail_path = os.path.join(comic_page_dir, "_thumbnail.jpg")
        if comic_info.getboolean(section, "Overwrite existing images") or not os.path.isfile(thumbnail_path):
            print(f"Creating thumbnail for {comic_page_name}")
            thumb_im = resize(im, comic_info.get(section, "Thumbnail size"))
            save_image(thumb_im, thumbnail_path)


def process_comic_images(comic_info: RawConfigParser, comic_data_dicts: List[Dict]):
    if comic_info.getboolean("Image Reprocessing", "Create thumbnails"):
        for comic_data in comic_data_dicts:
            if not comic_data["comic_paths"]:
                raise ValueError(
                    f"No images found for page '{comic_data['page_name']}'. Either add an image for that page, or disable "
                    f"the 'Create thumbnails' option in the [Image Reprocessing] section."
                )
            create_comic_thumbnail(comic_info, comic_data["comic_paths"][0])
