import io
import json
import tempfile
from pathlib import Path
from configparser import RawConfigParser
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from core import utils
from integrations import webring
from build.content.comic_config_sources import comic_config_data_to_legacy_parser, legacy_parser_to_comic_config_data

ROOT = Path(__file__).resolve().parents[2]
MEMBER = {'id': 'a', 'name': "A & B's comic", 'url': 'https://example.com/', 'image': ''}
DATA = {'version': 1, 'members': [MEMBER, dict(MEMBER, id='b'), dict(MEMBER, id='c')]}


class TestWebring(TestCase):
    def setUp(self):
        self.config = RawConfigParser()
        self.config.read_dict({'Webring': {'Enable webring': 'True', 'Endpoint': 'https://example.com/ring', 'Webring ID': 'b'}})

    def load(self, data=None):
        with patch.object(webring, 'fetch_data', return_value=deepcopy(DATA if data is None else data)):
            return webring.load_webring_data(self.config, '')

    def render(self, data, all_members=True):
        self.config.set('Webring', 'Show all members', str(all_members))
        utils.build_jinja_environment(self.config, [str(ROOT / 'templates')])
        return utils.jinja_environment.get_template('webring.tpl').render(**self.load(data))

    def test_disabled_does_not_fetch(self):
        self.config.set('Webring', 'Enable webring', 'False')
        with patch.object(webring, 'fetch_data') as fetch:
            self.assertEqual({'enable_webring': False}, webring.load_webring_data(self.config, ''))
            fetch.assert_not_called()

    def test_navigation_wraps_and_all_members_excludes_self(self):
        for own, previous, following in [('a', 'c', 'b'), ('b', 'a', 'c'), ('c', 'b', 'a')]:
            self.config.set('Webring', 'Webring ID', own)
            context = self.load()
            self.assertEqual(previous, context['webring_prev']['id'])
            self.assertEqual(following, context['webring_next']['id'])
        self.config.set('Webring', 'Show all members', 'True')
        self.config.set('Webring', 'Exclude own comic from members', 'True')
        self.assertEqual(['a', 'b'], [m['id'] for m in self.load()['webring_members']])

    def test_default_escapes_external_fields_in_both_layouts(self):
        attack = '<script>review_marker()</script>'
        data = deepcopy(DATA)
        data['label'] = attack
        data['home'] = dict(MEMBER, name=attack)
        data['members'][0].update(name=attack + '" onerror="review_marker()', image='https://example.com/x"')
        for all_members in [True, False]:
            # Both the plain attribute and URL must escape quotes.
            html = self.render(data, all_members)
            self.assertNotIn('<script>', html)
            self.assertIn('&lt;script&gt;', html)
            self.assertNotIn('" onerror="', html)

    def test_markdown_sanitizes_and_attributes_remain_literal(self):
        self.config.set('Webring', 'Text mode', 'markdown')
        data = deepcopy(DATA)
        payload = '**Bold** <script>bad()</script><img src=x onerror=bad()><svg onload=bad()>x</svg> [click](javascript:bad())'
        data['label'] = payload
        data['members'][0]['name'] = payload
        data['home'] = dict(MEMBER, name='**Home**', image='https://example.com/icon.png')
        html = self.render(data)
        self.assertIn('<strong>Bold</strong>', html)
        self.assertNotIn('<script', html)
        self.assertNotIn('<svg', html)
        self.assertNotIn('onerror=', html)
        self.assertNotIn('javascript:', html)
        self.assertIn('title="**Home**"', html)
        self.assertNotIn('<p>', html)

    def test_raw_html_requires_owner_option_and_warns(self):
        data = deepcopy(DATA)
        data['label'] = '<script>review_marker()</script>'
        data['text_mode'] = 'unsafe_html'
        self.assertNotIn('<script>', self.render(data))
        self.config.set('Webring', 'Text mode', 'unsafe_html')
        with self.assertLogs('integrations.webring', level='WARNING'):
            html = self.render(data)
        self.assertIn('<script>review_marker()</script>', html)

    def test_urls_rejected_in_every_mode(self):
        for mode in ['text', 'markdown', 'unsafe_html']:
            for url in ['javascript:alert(1)', 'data:text/html,x', '//example.com', 'https://a\\b', 'https://a\n', 'file:///tmp/a']:
                with self.subTest(mode=mode, url=url):
                    self.config.set('Webring', 'Text mode', mode)
                    data = deepcopy(DATA)
                    data['members'][0]['url'] = url
                    with self.assertRaises(ValueError):
                        self.load(data)

    def test_schema_failures_and_missing_self_abort_or_omit(self):
        invalid = [[], {}, {'version': True, 'members': [MEMBER]}, {'version': 1, 'members': []},
                   {'version': 1, 'members': [MEMBER, MEMBER]},
                   {'version': 1, 'members': [dict(MEMBER, name=2)]},
                   {'version': 1, 'members': [MEMBER]}]
        for data in invalid:
            self.config.set('Webring', 'On error', 'abort')
            with self.assertRaises(ValueError):
                self.load(data)
            self.config.set('Webring', 'On error', 'omit')
            with self.assertLogs('integrations.webring', level='WARNING'):
                self.assertEqual({'enable_webring': False}, self.load(data))

    def test_invalid_config_never_silently_omitted(self):
        self.config.set('Webring', 'On error', 'omit')
        for option, value in [('Text mode', 'typo'), ('On error', 'typo'), ('Endpoint', ''), ('Endpoint', 'file:///private'), ('Webring ID', '')]:
            with self.subTest(option=option):
                previous = self.config.get('Webring', option, fallback=None)
                self.config.set('Webring', option, value)
                with self.assertRaises(ValueError):
                    self.load()
                if previous is None:
                    self.config.remove_option('Webring', option)
                else:
                    self.config.set('Webring', option, previous)

    def test_toml_options_round_trip(self):
        config = comic_config_data_to_legacy_parser({'webring': {'text_mode': 'markdown', 'on_error': 'omit'}})
        self.assertEqual('markdown', config.get('Webring', 'Text mode'))
        self.assertEqual('omit', legacy_parser_to_comic_config_data(config)['webring']['on_error'])

    def test_local_json_and_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'ring.json'
            path.write_text(json.dumps(DATA), encoding='utf-8')
            with patch.object(webring, 'WEBRING_JSON', path), patch.object(webring, 'urlopen') as fetch:
                self.assertEqual(DATA, webring.fetch_data('local'))
                fetch.assert_not_called()
        with self.assertRaisesRegex(ValueError, 'exceeds'):
            webring.read_json(io.BytesIO(b' ' * (webring.MAX_RESPONSE_BYTES + 1)))
        with self.assertRaises(TimeoutError):
            webring.read_json(io.BytesIO(b'{}'), deadline=0)
        with self.assertRaises(ValueError):
            webring.read_json(io.BytesIO(b'not JSON'))

    def test_network_success_and_invalid_payload_not_retried(self):
        response = io.BytesIO(json.dumps(DATA).encode())
        response.geturl = lambda: 'https://example.com/ring'
        with patch.object(webring, 'urlopen', return_value=response) as fetch:
            self.assertEqual(DATA, webring.fetch_data('https://example.com/ring'))
            self.assertEqual(1, fetch.call_count)
        response = io.BytesIO(b'invalid JSON')
        response.geturl = lambda: 'https://example.com/ring'
        with patch.object(webring, 'urlopen', return_value=response) as fetch:
            with self.assertRaises(ValueError):
                webring.fetch_data('https://example.com/ring')
            self.assertEqual(1, fetch.call_count)

    def test_optional_names_and_images_default_to_empty_text(self):
        data = {'version': 1, 'members': [{'id': 'b', 'url': 'https://example.com/'}]}
        member = self.load(data)['webring_prev']
        self.assertEqual('', member['name'])
        self.assertEqual('', member['name_html'])
        self.assertEqual('', member['image'])

    def test_network_timeout_retry_and_permanent_failure(self):
        with patch.object(webring, 'urlopen', side_effect=URLError('offline')) as fetch:
            with self.assertRaises(URLError):
                webring.fetch_data('https://example.com/ring')
            self.assertEqual(2, fetch.call_count)
            fetch.assert_called_with('https://example.com/ring', timeout=10)
        with patch.object(webring, 'urlopen', side_effect=HTTPError('https://example.com', 404, 'missing', {}, None)) as fetch:
            with self.assertRaises(HTTPError):
                webring.fetch_data('https://example.com/ring')
            self.assertEqual(1, fetch.call_count)
        with patch.object(webring, 'fetch_data', side_effect=URLError('offline')):
            with self.assertRaises(ValueError):
                webring.load_webring_data(self.config, '')
            self.config.set('Webring', 'On error', 'omit')
            with self.assertLogs('integrations.webring', level='WARNING'):
                self.assertEqual({'enable_webring': False}, webring.load_webring_data(self.config, ''))
