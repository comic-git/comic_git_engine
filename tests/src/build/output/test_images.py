import os
import tempfile
from configparser import RawConfigParser
from unittest import TestCase
from unittest.mock import MagicMock, patch

from build.output import images


MUT = "build.output.images."


class TestImageUtils(TestCase):

    def test_resize_set_size(self):
        im = MagicMock()
        im.size = 100, 200
        self.assertEqual(im.resize.return_value, images.resize(im, " 150, 350 "))
        im.resize.assert_called_once_with((150, 350))

    def test_resize_percentage(self):
        im = MagicMock()
        im.size = 100, 200
        self.assertEqual(im.resize.return_value, images.resize(im, "50%"))
        im.resize.assert_called_once_with((50, 100))

    def test_resize_set_height(self):
        im = MagicMock()
        im.size = 100, 200
        self.assertEqual(im.resize.return_value, images.resize(im, "220h"))
        im.resize.assert_called_once_with((110, 220))

    def test_resize_set_width(self):
        im = MagicMock()
        im.size = 100, 200
        self.assertEqual(im.resize.return_value, images.resize(im, "110w"))
        im.resize.assert_called_once_with((110, 220))

    def test_resize_exception(self):
        im = MagicMock()
        im.size = 100, 200
        with self.assertRaisesRegex(ValueError, "Unknown resize value:"):
            images.resize(im, "farts lol")
        im.resize.assert_not_called()

    def test_save_image_converts_non_rgb_before_jpeg_save(self):
        im = MagicMock()
        im.mode = "RGBA"
        converted = MagicMock()
        im.convert.return_value = converted

        images.save_image(im, "page.jpg")

        im.convert.assert_called_once_with("RGB")
        converted.save.assert_called_once_with("page.jpg")

    @patch(MUT + "Image.new")
    def test_save_image_uses_transparency_fallback(self, mock_new):
        im = MagicMock()
        im.mode = "RGB"
        im.size = (10, 10)
        im.save.side_effect = OSError("cannot write mode RGBA as JPEG")
        bg = MagicMock()
        mock_new.return_value = bg

        images.save_image(im, "page.jpg")

        bg.paste.assert_called_once_with(im, (0, 0), im)
        bg.save.assert_called_once_with("page.jpg")

    def make_comic_info(self, overwrite=False, create_thumbnails=True):
        comic_info = RawConfigParser()
        comic_info.add_section("Image Reprocessing")
        comic_info.set("Image Reprocessing", "Create thumbnails", str(create_thumbnails))
        comic_info.set("Image Reprocessing", "Overwrite existing images", str(overwrite))
        comic_info.set("Image Reprocessing", "Thumbnail size", "50%")
        return comic_info

    @patch(MUT + "save_image")
    @patch(MUT + "resize")
    @patch(MUT + "Image.open")
    def test_create_comic_thumbnail_respects_overwrite_setting(self, mock_open_image, mock_resize, mock_save_image):
        comic_info = self.make_comic_info(overwrite=False)
        with tempfile.TemporaryDirectory() as temp_dir:
            comic_page_path = os.path.join(temp_dir, "page.png")
            thumbnail_path = os.path.join(temp_dir, "_thumbnail.jpg")
            with open(comic_page_path, "wb") as f:
                f.write(b"img")
            with open(thumbnail_path, "wb") as f:
                f.write(b"existing")

            images.create_comic_thumbnail(comic_info, comic_page_path)

            mock_resize.assert_not_called()
            mock_save_image.assert_not_called()

            comic_info.set("Image Reprocessing", "Overwrite existing images", "True")
            images.create_comic_thumbnail(comic_info, comic_page_path)

        mock_open_image.assert_called()
        mock_resize.assert_called_once()
        mock_save_image.assert_called_once()

    @patch(MUT + "create_comic_thumbnail")
    def test_process_comic_images_calls_thumbnail_on_first_image_only(self, mock_create_thumbnail):
        comic_info = self.make_comic_info()
        comic_data_dicts = [
            {"page_name": "001", "comic_paths": ["first.png", "second.png"]},
        ]

        images.process_comic_images(comic_info, comic_data_dicts)

        mock_create_thumbnail.assert_called_once_with(comic_info, "first.png")

    def test_process_comic_images_raises_when_page_has_no_images(self):
        comic_info = self.make_comic_info()

        with self.assertRaisesRegex(ValueError, "No images found for page '001'"):
            images.process_comic_images(comic_info, [{"page_name": "001", "comic_paths": []}])
