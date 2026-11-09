"""Real host/CLI checks for publication selection and source thumbnail caching."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase

from PIL import Image

ENGINE = Path(__file__).resolve().parents[2]


class TestSelectiveStagingCLI(TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.host = Path(temp.name)
        for name in ('css', 'js', 'schemas', 'templates'):
            shutil.copytree(ENGINE / name, self.host / 'comic_git_engine' / name)
        self.config = (
            '[Comic Info]\nComic name = Test\nAuthor = Artist\nDescription = Test\n'
            '[Comic Settings]\nComic domain = https://example.invalid\nComic subdirectory =\n'
            'Timezone = UTC\nDate format = %B %d, %Y\nExtra comics = extras/story\n'
            '[Archive]\nUse thumbnails = true\n'
            '[Image Reprocessing]\nCreate thumbnails = true\nThumbnail size = 20w\n'
            '[Transcripts]\nEnable transcripts = false\n[Links Bar]\n[Pages]\nindex = Home\n'
        )
        self.write('your_content/comic_info.ini', self.config)
        self.write('your_content/extras/story/comic_info.ini', '[Comic Info]\nComic name = Extra\n[Pages]\nindex = Home\n')
        for base in ('your_content', 'your_content/extras/story'):
            self.page(base + '/comics/ready', '2020-01-01')
            self.page(base + '/comics/future', '2099-01-01')
            self.write(base + '/comics/incomplete/info.toml', 'title = "Unfinished"\n')
            self.write(base + '/comics/no-metadata/asset.txt', 'unfinished')
            self.write(base + '/comics/loose.txt', 'loose')
            self.write(base + '/banner.txt', 'shared')
        self.page('your_content/comics/.hidden', '2020-01-01')
        self.write('your_content/comics/ready/.notes', 'notes')
        self.write('your_content/site_root/.htaccess', 'rules')
        self.write('your_content/.secret', 'private')
        self.write('your_content/assets/.nested/file.txt', 'hidden subtree')
        self.write('your_content/unconfigured/comics/data.txt', 'ordinary asset')

    def write(self, name, text):
        path = self.host / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def page(self, folder, date):
        self.write(folder + '/info.toml', f'post_date = "{date}"\n[[images]]\nfilename = "image.png"\n')
        Image.new('RGB', (80, 40), 'red').save(self.host / folder / 'image.png')

    def build(self, *args, succeeds=True):
        env = {key: value for key, value in os.environ.items()
               if key not in ('INPUTS', 'SECRETS', 'OUTPUT_DIR', 'PYTHONPATH', 'GITHUB_REPOSITORY')}
        result = subprocess.run([sys.executable, '-B', str(ENGINE / 'src/build/build_site.py'), *args],
                                cwd=self.host, env=env, capture_output=True, text=True)
        if succeeds:
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        else:
            self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
        return result

    def snapshot(self):
        return {path.relative_to(self.host).as_posix(): path.read_bytes()
                for path in (self.host / 'your_content').rglob('*') if path.is_file()}

    def test_selection_extra_comics_and_source_thumbnail_cache(self):
        before = self.snapshot()
        result = self.build('--selective-copy', '--delete-scheduled-posts')
        self.assertIn('Skipping incomplete', result.stderr)
        self.assertIn('does not delete scheduled', result.stderr)
        output = self.host / 'build'
        for base, html_base in [('your_content', ''), ('your_content/extras/story', 'extras/story/')]:
            self.assertTrue((output / (html_base + 'comic/ready/index.html')).is_file())
            for skipped in ('future', 'incomplete', 'no-metadata'):
                self.assertFalse((output / base / 'comics' / skipped).exists())
                self.assertFalse((output / (html_base + f'comic/{skipped}')).exists())
            self.assertFalse((output / base / 'comics/loose.txt').exists())
            self.assertTrue((output / base / 'banner.txt').is_file())
            source_thumb = self.host / base / 'comics/ready/_thumbnail.jpg'
            self.assertTrue(source_thumb.is_file())
            self.assertEqual(source_thumb.read_bytes(), (output / base / 'comics/ready/_thumbnail.jpg').read_bytes())
            self.assertFalse((self.host / base / 'comics/future/_thumbnail.jpg').exists())
            metadata = json.loads((output / (html_base + 'comic/page_info_list.json')).read_text())
            self.assertEqual(1, metadata['scheduled_post_count'])
            self.assertNotIn('future/image.png', json.dumps(metadata))
        for name, data in before.items():
            self.assertEqual(data, (self.host / name).read_bytes(), name)
        self.assertTrue((output / 'your_content/unconfigured/comics/data.txt').is_file())
        for name in ('your_content/.secret', 'your_content/assets/.nested', '.htaccess',
                     'your_content/comics/ready/.notes', 'your_content/comics/.hidden'):
            self.assertFalse((output / name).exists(), name)
        thumb = self.host / 'your_content/comics/ready/_thumbnail.jpg'
        timestamp = thumb.stat().st_mtime_ns
        self.build('--selective-copy')
        self.assertEqual(timestamp, thumb.stat().st_mtime_ns)

    def test_python_cache_directories_stay_out_of_selective_output(self):
        caches = (
            'your_content/themes/default/scripts/__pycache__',
            'your_content/comics/ready/__pycache__',
            'your_content/site_root/assets/__pycache__',
        )
        for cache in caches:
            self.write(cache + '/helper.cpython-314.pyc', 'bytecode')
        self.write('your_content/themes/default/css/theme.css', 'body {}')
        self.write('your_content/site_root/assets/keep.txt', 'asset')
        self.write('your_content/comic_info.ini', self.config + '[Build]\nInclude hidden files = true\n')

        self.build('--selective-copy')

        output = self.host / 'build'
        self.assertEqual([], list(output.rglob('__pycache__')))
        for cache in caches:
            self.assertTrue((self.host / cache / 'helper.cpython-314.pyc').is_file(), cache)
        self.assertTrue((output / 'your_content/themes/default/css/theme.css').is_file())
        self.assertTrue((output / 'your_content/comics/ready/image.png').is_file())
        self.assertTrue((output / 'assets/keep.txt').is_file())

    def test_hidden_include_all_and_explicit_allowlist_precedence(self):
        self.write('your_content/comic_info.ini', self.config + '[Build]\nSelective copy = true\nInclude hidden files = true\n')
        self.build()
        for name in ('your_content/.secret', 'your_content/comics/ready/.notes',
                     'your_content/comics/.hidden/image.png', '.htaccess'):
            self.assertTrue((self.host / 'build' / name).is_file(), name)
        self.build('--hidden-paths', '.htaccess')
        self.assertTrue((self.host / 'build/.htaccess').is_file())
        self.assertFalse((self.host / 'build/your_content/.secret').exists())
        self.assertFalse((self.host / 'build/your_content/comics/.hidden').exists())

    def test_publish_all_includes_future_and_generates_its_thumbnail(self):
        self.build('--selective-copy', '--publish-all-comics', '--delete-scheduled-posts')
        self.assertTrue((self.host / 'build/comic/future/index.html').is_file())
        self.assertTrue((self.host / 'build/your_content/comics/future/_thumbnail.jpg').is_file())
        self.assertTrue((self.host / 'your_content/comics/future/info.toml').is_file())

    def test_malformed_input_fails_even_when_other_required_values_are_missing(self):
        self.write('your_content/comics/incomplete/info.toml', 'title = 123\n')
        before = self.snapshot()
        result = self.build('--selective-copy', succeeds=False)
        self.assertIn("Expected 'title'", result.stderr)
        for name, data in before.items():
            self.assertEqual(data, (self.host / name).read_bytes())

    def test_invalid_output_fails_before_cleanup_or_thumbnail_generation(self):
        sentinel = self.write('your_content/keep.txt', 'keep')
        self.build('--selective-copy', '--output-dir', 'your_content', succeeds=False)
        self.assertEqual('keep', sentinel.read_text())
        self.assertFalse((self.host / 'your_content/comics/ready/_thumbnail.jpg').exists())

    def test_explicit_hidden_image_fails_instead_of_rendering_a_broken_link(self):
        self.write('your_content/comics/ready/info.toml', 'post_date = "2020-01-01"\n[[images]]\nfilename = ".image.png"\n')
        shutil.copyfile(self.host / 'your_content/comics/ready/image.png',
                        self.host / 'your_content/comics/ready/.image.png')
        result = self.build('--selective-copy', succeeds=False)
        self.assertIn('hidden-path policy', result.stderr)

    def test_legacy_override_retains_wholesale_copy_behavior(self):
        # Missing required values fail in legacy mode, so remove only those fixtures.
        for base in ('your_content', 'your_content/extras/story'):
            shutil.rmtree(self.host / base / 'comics/incomplete')
        self.write('your_content/comic_info.ini', self.config + '[Build]\nSelective copy = true\n')
        self.write('your_content/themes/default/scripts/__pycache__/helper.cpython-314.pyc', 'bytecode')
        self.build('--no-selective-copy')
        self.assertTrue((self.host / 'build/your_content/themes/default/scripts/__pycache__').is_dir())
        self.assertTrue((self.host / 'build/your_content/comics/future/image.png').is_file())
        self.assertTrue((self.host / 'build/your_content/comics/loose.txt').is_file())
        self.assertTrue((self.host / 'build/your_content/.secret').is_file())

    def test_source_overwrite_is_copied_and_hook_identity_changes_fail(self):
        thumbnail = self.host / 'your_content/comics/ready/_thumbnail.jpg'
        Image.new('RGB', (10, 10), 'blue').save(thumbnail)
        before = thumbnail.read_bytes()
        self.write('your_content/comic_info.ini', self.config.replace('Create thumbnails = true',
                   'Create thumbnails = true\nOverwrite existing images = true'))
        self.build('--selective-copy')
        self.assertNotEqual(before, thumbnail.read_bytes())
        self.assertEqual(thumbnail.read_bytes(), (self.host / 'build/your_content/comics/ready/_thumbnail.jpg').read_bytes())
        self.write('your_content/themes/default/scripts/hooks.py',
                   'def extra_comic_dict_processing(folder, config, page):\n'
                   '    page.page_dir = "your_content/comics/future/"\n    return page\n')
        result = self.build('--selective-copy', succeeds=False)
        self.assertIn('changed the selected page folder', result.stderr)
        self.assertFalse((self.host / 'your_content/comics/future/_thumbnail.jpg').exists())

    def test_legacy_auto_images_respect_hidden_policy_and_missing_ini_values_skip(self):
        folder = self.host / 'your_content/comics/ready'
        (folder / 'info.toml').unlink()
        self.write('your_content/comics/ready/info.ini', 'Post date = January 01, 2020\n')
        shutil.copyfile(folder / 'image.png', folder / '.hidden.png')
        self.write('your_content/comics/incomplete/info.ini', 'Title = Unfinished\n')
        (self.host / 'your_content/comics/incomplete/info.toml').unlink()
        self.build('--selective-copy')
        metadata = (self.host / 'build/comic/page_info_list.json').read_text()
        self.assertNotIn('.hidden.png', metadata)
        self.assertIn('image.png', metadata)
        self.write('your_content/comic_info.ini', self.config + '[Build]\nInclude hidden files = true\n')
        self.build('--selective-copy')
        self.assertIn('.hidden.png', (self.host / 'build/comic/page_info_list.json').read_text())

    def test_missing_declared_filename_skips_but_invalid_supplied_values_fail(self):
        self.write('your_content/comics/incomplete/info.toml',
                   'post_date = "2020-01-01"\n[[images]]\ntitle = "Unfinished"\n')
        self.build('--selective-copy')
        self.assertFalse((self.host / 'build/your_content/comics/incomplete').exists())
        self.write('your_content/comics/incomplete/info.toml',
                   '[[images]]\nfilename = "missing.png"\n')
        result = self.build('--selective-copy', succeeds=False)
        self.assertIn('must be a file', result.stderr)

    def test_loose_files_and_unselected_pages_cannot_be_restored_by_allowlist(self):
        self.write('your_content/comics/.loose', 'loose')
        result = self.build('--selective-copy', '--hidden-paths', 'your_content/comics/.loose', succeeds=False)
        self.assertIn('Included hidden path does not exist', result.stderr)
        self.assertFalse((self.host / 'build/your_content/comics/.loose').exists())

    def test_hidden_page_allowlist_covers_assets_and_generated_html(self):
        self.build('--selective-copy', '--hidden-paths',
                   'your_content/comics/.hidden\ncomic/.hidden')
        self.assertTrue((self.host / 'build/comic/.hidden/index.html').is_file())
        self.assertTrue((self.host / 'build/your_content/comics/.hidden/image.png').is_file())

    def test_source_links_are_rejected_before_thumbnail_writes(self):
        folder = self.host / 'your_content/comics/ready'
        try:
            (folder / 'linked.png').symlink_to(folder / 'image.png')
        except OSError:
            self.skipTest('Creating symlinks is unavailable on this host')
        result = self.build('--selective-copy', succeeds=False)
        self.assertIn('symlinks or junctions', result.stderr)
        self.assertFalse((folder / '_thumbnail.jpg').exists())
