import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from scripts import deploy_sftp


class TestLocalSftpDeployment(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.host = Path(directory.name)
        self.host_engine = self.host / "comic_git_engine"
        for name in ("templates", "css", "js", "schemas"):
            shutil.copytree(deploy_sftp.ENGINE_ROOT / name, self.host_engine / name)
        content = self.host / "your_content"
        (content / "site_root").mkdir(parents=True)
        (content / "site_root/.htaccess").write_text("rules", encoding="utf-8")
        (content / "site_root/.private").write_text("private", encoding="utf-8")
        (content / "comic_info.ini").write_text(
            "[Comic Info]\nComic name = Comic\nAuthor = Artist\nDescription = Test\n"
            "[Comic Settings]\nComic domain = https://example.invalid\nComic subdirectory =\n"
            "Timezone = UTC\nDate format = %B %d, %Y\n"
            "[Archive]\nUse thumbnails = false\n[Transcripts]\nEnable transcripts = false\n"
            "[Links Bar]\n[Pages]\nindex = Home\n",
            encoding="utf-8",
        )
        for page, date in (("ready", "2020-01-01"), ("scheduled", "2099-01-01")):
            folder = content / "comics" / page
            folder.mkdir(parents=True)
            (folder / "info.toml").write_text(f'post_date = {date}\ntitle = "{page}"\n', encoding="utf-8")
            (folder / "asset.txt").write_text(page, encoding="utf-8")
        self.env = {
            **os.environ,
            "SFTP_HOST": "example.invalid",
            "SFTP_REMOTE_DIR": "/home/artist/comic.example",
            "SFTP_USERNAME": "artist",
            "SFTP_PASSWORD": "fixture-password",
            "SFTP_PRIVATE_KEY": "",
            "SFTP_KNOWN_HOSTS": "example.invalid ssh-ed25519 fixture-key",
            "SFTP_HIDDEN_PATHS": ".htaccess",
            "SFTP_CLEAN": "false",
            "SFTP_EXCLUDE_PATHS": ".well-known",
            "INPUTS": f"OUTPUT_DIR:{self.host / 'build'}",
        }

    def test_local_build_omits_scheduled_sources_from_upload(self):
        preview = self.host / "build"
        preview.mkdir()
        (preview / "preview.txt").write_text("preview", encoding="utf-8")
        (self.host_engine / "templates/index.tpl").write_text("<!-- host template -->", encoding="utf-8")
        (self.host_engine / "css/base.css").write_text("/* host stylesheet */", encoding="utf-8")

        def inspect_transfer(output, config, env):
            site = Path(output)
            self.assertIn("<!-- host template -->", (site / "index.html").read_text(encoding="utf-8"))
            self.assertTrue((site / "comic/ready/index.html").is_file())
            self.assertEqual("/* host stylesheet */",
                             (site / "comic_git_engine/css/base.css").read_text(encoding="utf-8"))
            self.assertTrue((site / "comic_git_engine/js/comic.js").is_file())
            self.assertTrue((site / "comic_git_engine/schemas/page_info_list.schema.json").is_file())
            self.assertTrue((site / "your_content/comics/ready/asset.txt").is_file())
            self.assertFalse((site / "comic/scheduled").exists())
            self.assertFalse((site / "your_content/comics/scheduled").exists())
            self.assertTrue((site / ".htaccess").is_file())
            self.assertFalse((site / ".private").exists())
            self.assertEqual((".well-known",), config.exclusions)
            self.assertFalse(config.clean)
            self.assertEqual("fixture-password", env["SFTP_PASSWORD"])

        with patch.object(deploy_sftp, "deploy", side_effect=inspect_transfer) as transfer:
            deploy_sftp.build_and_deploy(self.host, self.env)

        transfer.assert_called_once()
        output = transfer.call_args.args[0]
        self.assertFalse(output.parent.exists())
        self.assertTrue((self.host / "your_content/comics/scheduled/asset.txt").is_file())
        self.assertTrue((preview / "preview.txt").is_file())

    def test_build_failure_skips_transfer_and_discards_staging(self):
        error = subprocess.CalledProcessError(1, "build_site.py")
        with (
            patch.object(deploy_sftp.subprocess, "run", side_effect=error) as build,
            patch.object(deploy_sftp, "deploy") as transfer,
            self.assertRaises(subprocess.CalledProcessError),
        ):
            deploy_sftp.build_and_deploy(self.host, self.env)

        transfer.assert_not_called()
        self.assertEqual(self.host, build.call_args.kwargs['cwd'])
        command = build.call_args.args[0]
        output = Path(command[command.index('--output-dir') + 1])
        self.assertFalse(output.parent.exists())
        self.assertIn('--selective-copy', command)
        self.assertIn('-B', command)
        self.assertNotIn('--delete-scheduled-posts', command)
        self.assertNotIn("SFTP_PASSWORD", build.call_args.kwargs["env"])
        self.assertNotIn("INPUTS", build.call_args.kwargs["env"])

    def test_help_runs_directly(self):
        script = deploy_sftp.ENGINE_ROOT / "src/scripts/deploy_sftp.py"
        result = subprocess.run([sys.executable, "-S", str(script), "--help"], cwd=self.host,
                                capture_output=True, text=True)
        self.assertEqual(0, result.returncode, msg=result.stderr)
        self.assertIn("SFTP_KNOWN_HOSTS", result.stdout)
        self.assertIn("--verbose", result.stdout)
        self.assertIn("--upload-only", result.stdout)
        self.assertNotIn("--publish-all-comics", result.stdout)

    def test_upload_only_requires_a_built_index_before_connecting(self):
        with (
            patch.object(deploy_sftp, "require_paramiko"),
            patch("build.output.local_sftp.require_paramiko") as connect,
            patch.dict(os.environ, self.env, clear=True),
            self.assertRaisesRegex(ValueError, "without a built index.html"),
        ):
            deploy_sftp.main(["--upload-only", str(self.host)])
        connect.assert_not_called()

    def test_build_uses_real_host_context(self):
        self.write_host_hook()
        with patch.object(deploy_sftp, 'deploy') as transfer:
            deploy_sftp.build_and_deploy(self.host, self.env)
        transfer.assert_called_once()
        self.assertEqual('host data', (self.host / 'hook-saw-host.txt').read_text())

    def write_host_hook(self):
        (self.host / 'host-data.txt').write_text('host data')
        scripts = self.host / 'your_content/themes/default/scripts'
        scripts.mkdir(parents=True)
        (scripts / 'hooks.py').write_text(
            'from pathlib import Path\n'
            'def preprocess(config):\n'
            '    Path("hook-saw-host.txt").write_text(Path("host-data.txt").read_text())\n'
        )
