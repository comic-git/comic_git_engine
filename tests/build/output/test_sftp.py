"""Check settings used by both SFTP entry points."""
from unittest import TestCase

from build.output.sftp import SftpConfig, deployment_credentials


class TestSftpConfig(TestCase):
    env = {
        "SFTP_HOST": "example.com",
        "SFTP_REMOTE_DIR": "/home/artist/comic.example/",
        "SFTP_USERNAME": "artist",
        "SFTP_PASSWORD": "fixture-password",
        "SFTP_KNOWN_HOSTS": "example.com ssh-ed25519 fixture-key",
    }

    def test_remote_path_defaults_and_exclusions(self):
        config = SftpConfig.from_environment({**self.env, "SFTP_REMOTE_DIR": "comic.example/",
                                             "SFTP_EXCLUDE_PATHS": ".well-known\nserver files"})
        self.assertEqual(SftpConfig("example.com", 22, "./comic.example", True,
                                    (".well-known", "server files")), config)

    def test_unsafe_connection_settings_fail_validation(self):
        for key, values in {
            "SFTP_HOST": ("sftp://host", "host;bye"),
            "SFTP_PORT": ("0", "65536", "22.5"),
            "SFTP_REMOTE_DIR": ("", "/", ".", "..", "/home/artist", "//home/artist",
                                "../site", "~/site", "site\nbye", "/var/www"),
            "SFTP_EXCLUDE_PATHS": ("../file", "/file", "./file"),
        }.items():
            for value in values:
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    SftpConfig.from_environment({**self.env, key: value})

    def test_credentials_require_a_user_host_key_and_one_authentication_method(self):
        for key in ("SFTP_USERNAME", "SFTP_KNOWN_HOSTS", "SFTP_PASSWORD"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                deployment_credentials({**self.env, key: ""})
        with self.assertRaises(ValueError):
            deployment_credentials({**self.env, "SFTP_PRIVATE_KEY": "fixture-key"})
