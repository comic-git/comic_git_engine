"""Test deployment preparation separately from credentials and the transfer."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from unittest import TestCase, skipUnless
from unittest.mock import patch

from build.output import sftp


class TestSftpDeployment(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'build'
        self.source.mkdir()
        self.bundle = self.root / 'deployment'
        (self.source / 'index.html').write_text('home')
        self.env = {
            'OUTPUT_DIR': str(self.source), 'RUNNER_TEMP': str(self.root),
            'GITHUB_OUTPUT': str(self.root / 'outputs'), 'SFTP_HIDDEN_PATHS': '',
            'SFTP_HOST': 'example.com', 'SFTP_PORT': '22',
            'SFTP_REMOTE_DIR': '/home/artist/comic.example/', 'SFTP_CLEAN': 'true',
            'SFTP_EXCLUDE_PATHS': '', 'SFTP_USERNAME': 'artist',
            'SFTP_PASSWORD': 'password with ; $ quotes " and \'', 'SFTP_PRIVATE_KEY': '',
            'SFTP_KNOWN_HOSTS': 'example.com ssh-ed25519 test-key',
        }

    def prepare(self):
        config = sftp.SftpConfig.from_environment(self.env)
        sftp.write_deployment_files(str(self.source), str(self.bundle), config)

    def run_deployment(self):
        self.prepare()
        sftp.deploy(str(self.bundle), str(self.source), {**os.environ, **self.env})

    def write_source(self, path, text='test'):
        target = self.source / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def test_preparation_needs_no_credentials_and_never_connects(self):
        secret_values = ['private-password-marker', 'private-key-marker', 'private-user-marker']
        self.env.update(SFTP_PASSWORD=secret_values[0], SFTP_PRIVATE_KEY=secret_values[1],
                        SFTP_USERNAME=secret_values[2])
        with patch('subprocess.run') as run:
            self.prepare()
        run.assert_not_called()
        self.assertEqual({'deploy.py', 'deploy.lftp', 'connection.json'},
                         {path.name for path in self.bundle.iterdir()})
        self.assertEqual({'index.html'}, {path.name for path in self.source.iterdir()})
        for path in self.bundle.iterdir():
            text = path.read_text()
            for secret in secret_values:
                self.assertNotIn(secret, text)
            self.assertNotIn(str(self.source), text)
        for name in ['SFTP_USERNAME', 'SFTP_PASSWORD', 'SFTP_PRIVATE_KEY', 'SFTP_KNOWN_HOSTS']:
            self.env.pop(name)
        self.prepare()

    def test_deployment_files_cannot_be_written_into_site_or_sources(self):
        config = sftp.SftpConfig.from_environment(self.env)
        for destination in [self.source, self.source / 'deployment', self.root,
                            Path.cwd(), Path.cwd() / 'your_content/deployment']:
            with self.subTest(destination=destination), self.assertRaises(ValueError):
                sftp.write_deployment_files(str(self.source), str(destination), config)
        self.assertEqual({'index.html'}, {path.name for path in self.source.iterdir()})

    def test_bundle_and_site_can_be_relocated_before_deployment(self):
        self.prepare()
        downloaded = self.root / 'downloaded'
        bundle = downloaded / 'scripts'
        site = downloaded / 'site'
        shutil.copytree(self.bundle, bundle)
        shutil.copytree(self.source, site)
        with patch('subprocess.run') as run:
            run.return_value.returncode = 0
            sftp.deploy(str(bundle), str(site), {**os.environ, **self.env})
        self.assertEqual(site.resolve(), run.call_args.kwargs['cwd'])
        self.assertIn('-- . .', run.call_args.kwargs['input'])
        self.assertNotIn(str(self.source), run.call_args.kwargs['input'])

    def test_bundled_runner_runs_without_engine_imports(self):
        self.prepare()
        env = os.environ.copy()
        env.pop('PYTHONPATH', None)
        env.update(SFTP_USERNAME='', SFTP_PASSWORD='', SFTP_PRIVATE_KEY='', SFTP_KNOWN_HOSTS='')
        result = subprocess.run([sys.executable, str(self.bundle / 'deploy.py'),
                                 '--output-dir', str(self.source)], cwd=self.root,
                                env=env, capture_output=True, text=True)
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Set SFTP_USERNAME', result.stderr)
        self.assertNotIn('ModuleNotFoundError', result.stderr)

    def test_empty_build_is_rejected_before_transfer(self):
        (self.source / 'index.html').unlink()
        with patch('subprocess.run') as run, self.assertRaises(ValueError):
            self.run_deployment()
        run.assert_not_called()

    def deploy(self):
        with patch('subprocess.run') as run:
            run.return_value.returncode = 0
            self.run_deployment()
        return run.call_args

    def test_password_deploy_cleans_and_pins_host_without_putting_password_in_script(self):
        call = self.deploy()
        commands = call.kwargs['input']
        self.assertEqual(['lftp', '--norc'], call.args[0])
        self.assertNotIn(self.env['SFTP_PASSWORD'], commands)
        self.assertEqual(self.env['SFTP_PASSWORD'], call.kwargs['env']['LFTP_PASSWORD'])
        self.assertIn('StrictHostKeyChecking=yes', commands)
        self.assertIn('PubkeyAuthentication=no', commands)
        self.assertIn('cd "/home/artist/comic.example"', commands)
        self.assertIn('--delete', commands)
        self.assertIn('--transfer-all', commands)
        self.assertIn('set cmd:fail-exit yes', commands)
        self.assertEqual([], list(self.root.glob('sftp-auth-*')))

    def test_key_auth_and_cleanup_disabled(self):
        self.env.update(SFTP_PASSWORD='', SFTP_PRIVATE_KEY='test-private-key', SFTP_CLEAN='false')
        commands = self.deploy().kwargs['input']
        self.assertIn('IdentitiesOnly=yes', commands)
        self.assertIn('BatchMode=yes', commands)
        self.assertNotIn('--delete', commands)
        self.assertNotIn('test-private-key', commands)
        self.assertEqual([], list(self.root.glob('sftp-auth-*')))

    def test_relative_remote_directory_and_exclusions(self):
        self.env.update(SFTP_REMOTE_DIR='comic.example/', SFTP_EXCLUDE_PATHS='.well-known\nserver files')
        commands = self.deploy().kwargs['input']
        self.assertIn('cd "./comic.example"', commands)
        self.assertIn('--exclude', commands)
        self.assertNotIn('--delete-excluded', commands)

    def test_invalid_configuration_never_contacts_server(self):
        invalid = [
            ('SFTP_HOST', 'sftp://host'), ('SFTP_HOST', 'host;bye'),
            ('SFTP_PORT', '0'), ('SFTP_PORT', '65536'), ('SFTP_PORT', '22.5'),
            ('SFTP_USERNAME', ''), ('SFTP_KNOWN_HOSTS', ''), ('SFTP_PASSWORD', ''),
            ('SFTP_PRIVATE_KEY', 'key-while-password-is-set'),
        ]
        invalid += [('SFTP_REMOTE_DIR', path) for path in ['', '/', '.', '..', '/home/artist', '//home/artist', '../site', '~/site', 'site\nbye', '/var/www']]
        invalid += [('SFTP_EXCLUDE_PATHS', path) for path in ['../file', '/file', './file']]
        original = self.env.copy()
        for setting, value in invalid:
            with self.subTest(setting=setting, value=value):
                self.env = {**original, setting: value}
                with patch('subprocess.run') as run, self.assertRaises(ValueError):
                    self.run_deployment()
                run.assert_not_called()

    def test_failed_transfer_fails_job_and_removes_credentials(self):
        with patch('subprocess.run') as run, self.assertRaisesRegex(RuntimeError, 'deployment failed'):
            run.return_value.returncode = 1
            self.run_deployment()
        self.assertEqual([], list(self.root.glob('sftp-auth-*')))

    @skipUnless(os.environ.get('LFTP_BINARY'), 'Set LFTP_BINARY to exercise the real client on Linux.')
    def test_real_lftp_mirror_updates_deletes_and_preserves_exclusions(self):
        remote = self.root / 'remote with spaces $dollar `tick` "quote" semi;'
        remote.mkdir()
        (remote / 'old.html').write_text('removed page')
        (remote / 'index.html').write_text('previous home')
        (remote / '.htaccess').write_text('old rules')
        protected = remote / '.well-known'
        protected.mkdir()
        (protected / 'token').write_text('host-managed')
        self.write_source('.htaccess', 'new rules')
        self.write_source('a $quote " semi; apostrophe\'/page.html', 'page')
        self.env.update(SFTP_REMOTE_DIR=remote.as_posix(), SFTP_EXCLUDE_PATHS='.well-known')
        real_run = subprocess.run

        def local_transfer(args, **kwargs):
            # Exercise the exact generated mirror command through lftp's local
            # transport. SSH/authentication still require a live-server test.
            commands = re.sub(r'^open .*$', 'open file:///', kwargs['input'], flags=re.MULTILINE)
            result = real_run([os.environ['LFTP_BINARY'], '--norc'], input=commands,
                              text=True, cwd=kwargs['cwd'], env=kwargs['env'], capture_output=True, timeout=30)
            if result.returncode:
                print(result.stderr)
            return result

        with patch('subprocess.run', side_effect=local_transfer):
            self.run_deployment()
            self.assertEqual('home', (remote / 'index.html').read_text())
            self.assertFalse((remote / 'old.html').exists())
            self.assertEqual('new rules', (remote / '.htaccess').read_text())
            self.assertEqual('host-managed', (protected / 'token').read_text())
            self.assertEqual('page', (remote / 'a $quote " semi; apostrophe\'/page.html').read_text())
            (remote / 'keep.html').write_text('keep')
            self.env['SFTP_CLEAN'] = 'false'
            self.run_deployment()
            self.assertTrue((remote / 'keep.html').exists())
            self.env['SFTP_REMOTE_DIR'] = (self.root / 'missing').as_posix()
            with self.assertRaises(RuntimeError):
                self.run_deployment()
            self.assertTrue((remote / 'keep.html').exists())
