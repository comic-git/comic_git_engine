import os
import tempfile
from configparser import RawConfigParser
from unittest import TestCase
from unittest.mock import MagicMock, patch

from build.output import images
from build.content.page_models import ComicImage, ComicPage


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
        comic_info.add_section("Archive")
        comic_info.set("Archive", "Entry mode", "Pages")
        comic_info.set("Archive", "Use thumbnails", "True")
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

            images.create_comic_thumbnail(comic_info, comic_page_path, thumbnail_path)

            mock_resize.assert_not_called()
            mock_save_image.assert_not_called()

            comic_info.set("Image Reprocessing", "Overwrite existing images", "True")
            images.create_comic_thumbnail(comic_info, comic_page_path, thumbnail_path)

        mock_open_image.assert_called()
        mock_resize.assert_called_once()
        mock_save_image.assert_called_once()

    def make_page(self, root, image_count=2):
        page_dir = os.path.join(root, "your_content", "comics", "001")
        os.makedirs(page_dir, exist_ok=True)
        comic_images = []
        for index in range(image_count):
            source_path = os.path.join(page_dir, f"page-{index}.png")
            with open(source_path, "wb") as f:
                f.write(b"image")
            comic_images.append(
                ComicImage(
                    id=f"main/001/page-{index}.png",
                    filename=f"page-{index}.png",
                    source_path=source_path,
                    web_path=source_path,
                    anchor_id=f"anchor-{index}",
                    title=f"Page {index}",
                    alt_text="",
                )
            )
        return ComicPage(
            id="main/001",
            comic_id="main",
            comic_folder="",
            page_name="001",
            page_dir=page_dir + os.sep,
            url="/comic/001/",
            title="Page",
            post_date="2024-01-01",
            display_post_date="January 01, 2024",
            archive_post_date="January 01, 2024",
            images=comic_images,
        )

    @patch(MUT + "create_comic_thumbnail")
    def test_page_mode_generates_only_page_thumbnail(self, mock_create_thumbnail):
        comic_info = self.make_comic_info()
        with tempfile.TemporaryDirectory() as temp_dir:
            page = self.make_page(temp_dir)
            page_target = os.path.join(page.page_dir, "_thumbnail.jpg").replace("\\", "/").strip("/")

            images.process_comic_images(comic_info, [page])

        mock_create_thumbnail.assert_called_once_with(
            comic_info,
            page.images[0].source_path,
            page_target,
        )

    @patch(MUT + "create_comic_thumbnail")
    def test_image_mode_generates_additional_identity_thumbnail(self, mock_create_thumbnail):
        comic_info = self.make_comic_info()
        comic_info.set("Archive", "Entry mode", "Images")
        with tempfile.TemporaryDirectory() as temp_dir:
            page = self.make_page(temp_dir)

            images.process_comic_images(comic_info, [page])

        self.assertEqual(2, mock_create_thumbnail.call_count)
        additional_target = mock_create_thumbnail.call_args_list[1].args[2]
        self.assertRegex(additional_target, r"_thumbnail_[0-9a-f]{64}\.jpg$")

    @patch(MUT + "create_comic_thumbnail")
    def test_explicit_and_blank_thumbnails_are_not_generated(self, mock_create_thumbnail):
        comic_info = self.make_comic_info()
        with tempfile.TemporaryDirectory() as temp_dir:
            page = self.make_page(temp_dir, image_count=1)
            page.thumbnail_path = "custom.jpg"
            page.thumbnail_explicit = True
            page.images[0].thumbnail_disabled = True

            images.process_comic_images(comic_info, [page])

        mock_create_thumbnail.assert_not_called()
        self.assertEqual("custom.jpg", page.thumbnail_path)
        self.assertIsNone(page.images[0].thumbnail_path)

    @patch(MUT + "create_comic_thumbnail")
    def test_no_image_page_uses_existing_page_thumbnail_without_generation(self, mock_create_thumbnail):
        comic_info = self.make_comic_info()
        with tempfile.TemporaryDirectory() as temp_dir:
            page = self.make_page(temp_dir, image_count=0)
            target = os.path.join(page.page_dir, "_thumbnail.jpg")
            with open(target, "wb") as f:
                f.write(b"thumbnail")

            images.process_comic_images(comic_info, [page])

        mock_create_thumbnail.assert_not_called()
        self.assertTrue(page.thumbnail_path.endswith("_thumbnail.jpg"))
