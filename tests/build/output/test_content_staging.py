import os
from configparser import RawConfigParser
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from build.output.content_staging import ContentCopyPolicy, resolve_copy_policy, managed_comic_roots, stage_remaining_content
from build import build_site


class TestCopyPolicy(TestCase):
    def config(self, **settings):
        config = RawConfigParser()
        config.read_dict({'Build': {k.replace('_', ' '): str(v) for k, v in settings.items()}})
        return config

    def test_legacy_and_selective_defaults(self):
        self.assertEqual(ContentCopyPolicy(False, None), resolve_copy_policy(self.config()))
        self.assertEqual(ContentCopyPolicy(True, ''), resolve_copy_policy(self.config(), selective_copy=True))

    def test_config_and_explicit_override(self):
        config = self.config(selective_copy=True)
        self.assertEqual(ContentCopyPolicy(True, ''), resolve_copy_policy(config))
        self.assertEqual(ContentCopyPolicy(False, None), resolve_copy_policy(config, selective_copy=False))
        self.assertEqual('', resolve_copy_policy(config, hidden_paths='').hidden_paths)

    def test_cli_boolean_override_is_tristate(self):
        self.assertIsNone(build_site.parse_args([]).selective_copy)
        self.assertTrue(build_site.parse_args(['--selective-copy']).selective_copy)
        self.assertFalse(build_site.parse_args(['--no-selective-copy']).selective_copy)

    def test_hidden_paths_use_final_output_paths(self):
        policy = ContentCopyPolicy(True, '.htaccess\nyour_content/comics/.draft')
        self.assertTrue(policy.allows('.htaccess'))
        self.assertFalse(policy.allows('your_content/site_root/.htaccess'))
        self.assertTrue(policy.allows('your_content/comics/.draft/image.png'))
        self.assertFalse(policy.allows('your_content/comics/ready/.notes'))


class TestContentStaging(TestCase):
    def test_managed_roots_reject_traversal_duplicates_and_page_nesting(self):
        with TemporaryDirectory() as directory, patch('os.getcwd', return_value=directory):
            for extras in [['../outside'], ['extras/story', 'extras/story'], ['comics/page'],
                           ['extras/story.'], ['extras/story ']]:
                with self.subTest(extras=extras), self.assertRaises(ValueError):
                    managed_comic_roots(extras)

    def test_general_copy_prunes_all_managed_comics_but_retains_auxiliary_assets(self):
        with TemporaryDirectory() as directory:
            old = os.getcwd()
            try:
                os.chdir(directory)
                for name in ['comics/loose.txt', 'comics/future/image.png',
                             'extras/comics/future/image.png',
                             'extras/story/comics/future/image.png', 'extras/story/banner.png',
                             'extras/story/other/comics/future.png', 'images/shared.png']:
                    path = Path('your_content') / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text('asset')
                roots = managed_comic_roots(['extras', 'extras/story'])
                stage_remaining_content('build', roots)
                self.assertFalse(Path('build/your_content/comics').exists())
                self.assertFalse(Path('build/your_content/extras/story/comics').exists())
                self.assertFalse(Path('build/your_content/extras/comics').exists())
                self.assertTrue(Path('build/your_content/extras/story/banner.png').is_file())
                self.assertTrue(Path('build/your_content/extras/story/other/comics/future.png').is_file())
                self.assertTrue(Path('build/your_content/images/shared.png').is_file())
            finally:
                os.chdir(old)
