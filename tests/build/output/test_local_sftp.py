
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from importlib.util import find_spec
from io import StringIO
import os
from pathlib import Path, PurePosixPath
import posixpath
import socket
import stat
from tempfile import TemporaryDirectory
from threading import Event
from types import SimpleNamespace
from unittest import TestCase, skipUnless
from unittest.mock import Mock, call

from build.output.local_sftp import deploy, mirror_site
from build.output.sftp import SftpConfig


def entry(filename, kind=stat.S_IFREG):
    return SimpleNamespace(filename=filename, st_mode=kind)


class TestMirrorSite(TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.source = Path(temp.name)
        (self.source / "index.html").write_text("new home", encoding="utf-8")
        self.client = Mock()
        self.client.lstat.return_value.st_mode = stat.S_IFDIR

    def test_cleanup_preserves_excluded_descendants_and_symlinks(self):
        self.client.listdir_attr.side_effect = {
            ".": [entry("index.html"), entry("old", stat.S_IFDIR),
                  entry("assets", stat.S_IFDIR), entry("alias", stat.S_IFLNK)],
            "old": [entry("nested", stat.S_IFDIR)],
            "old/nested": [entry("post.html")],
            "assets": [entry(".well-known", stat.S_IFDIR), entry("old.html")],
        }.__getitem__
        config = SftpConfig("example.invalid", 22, "/site", True, ("assets/.well-known",))
        mirror_site(self.client, self.source, config)
        self.client.put.assert_called_once_with(str(self.source / "index.html"), "index.html")
        self.assertEqual([call("old/nested/post.html"), call("assets/old.html")], self.client.remove.call_args_list)
        self.assertEqual([call("old/nested"), call("old")], self.client.rmdir.call_args_list)

    def test_upload_failure_leaves_obsolete_files_for_retry(self):
        self.client.listdir_attr.return_value = [entry("old.html")]
        self.client.put.side_effect = OSError("transfer interrupted")
        config = SftpConfig("example.invalid", 22, "/site", True, ())
        with self.assertRaisesRegex(OSError, "transfer interrupted"):
            mirror_site(self.client, self.source, config)
        self.client.remove.assert_not_called()

    def test_destination_collision_is_rejected_before_any_writes(self):
        self.client.listdir_attr.return_value = [entry("index.html", stat.S_IFLNK)]
        config = SftpConfig("example.invalid", 22, "/site", False, ())
        with self.assertRaisesRegex(ValueError, "incompatible file type"):
            mirror_site(self.client, self.source, config)
        self.client.put.assert_not_called()
        self.client.mkdir.assert_not_called()
        self.client.remove.assert_not_called()


@contextmanager
def sftp_server(root, host_key, login_key, attempts, *, allowed_auths="password,publickey",
                expect_host_rejection=False):
    import paramiko

    class Login(paramiko.ServerInterface):
        def get_allowed_auths(self, username):
            return allowed_auths

        def check_auth_password(self, username, password):
            attempts.append(username)
            return (paramiko.AUTH_SUCCESSFUL if (username, password) == ("artist", "fixture-password")
                    else paramiko.AUTH_FAILED)

        def check_auth_publickey(self, username, key):
            attempts.append(username)
            return paramiko.AUTH_SUCCESSFUL if username == "artist" and key == login_key else paramiko.AUTH_FAILED

        def check_channel_request(self, kind, _channel_id):
            return paramiko.OPEN_SUCCEEDED if kind == "session" else paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    class Files(paramiko.SFTPServerInterface):
        def path(self, name):
            relative = PurePosixPath(name.lstrip("/"))
            if ".." in relative.parts:
                raise ValueError("Path traversal in test request")
            return root.joinpath(*relative.parts)

        def canonicalize(self, name):
            return posixpath.normpath("/" + name.lstrip("/"))

        def stat(self, name):
            try:
                return paramiko.SFTPAttributes.from_stat(self.path(name).stat())
            except OSError as error:
                return paramiko.SFTPServer.convert_errno(error.errno)

        lstat = stat

        def list_folder(self, name):
            return [paramiko.SFTPAttributes.from_stat(item.stat(), item.name)
                    for item in self.path(name).iterdir()]

        def mkdir(self, name, _attributes):
            self.path(name).mkdir()
            return paramiko.SFTP_OK

        def open(self, name, flags, _attributes):
            handle = paramiko.SFTPHandle(flags)
            handle.writefile = os.fdopen(os.open(self.path(name), flags, 0o600), "wb")
            return handle

        def remove(self, name):
            self.path(name).unlink()
            return paramiko.SFTP_OK

    stop = Event()
    with socket.socket() as listener, ThreadPoolExecutor(max_workers=1) as pool:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        listener.settimeout(5)

        def serve():
            connection, _address = listener.accept()
            with connection, paramiko.Transport(connection) as transport:
                transport.add_server_key(host_key)
                transport.set_subsystem_handler("sftp", paramiko.SFTPServer, Files)
                try:
                    transport.start_server(server=Login())
                except (EOFError, ConnectionResetError):
                    if not expect_host_rejection:
                        raise
                    return
                channel = transport.accept(5)
                stop.wait(5)
                if channel is not None:
                    channel.close()

        running = pool.submit(serve)
        try:
            yield listener.getsockname()[1]
        finally:
            stop.set()
            running.result(timeout=10)


@skipUnless(find_spec("paramiko"), "Install requirements_sftp.txt to exercise the native SFTP connection.")
class TestNativeSftpConnection(TestCase):
    def test_auth_diagnostics_distinguish_rejected_password_from_unsupported_method(self):
        import paramiko

        server_key = paramiko.RSAKey.generate(2048)
        password = "test-password-that-must-stay-out-of-logs"
        with TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "index.html").write_text("home", encoding="utf-8")
            for methods, diagnostic in (
                ("password", "Authentication (password) failed"),
                ("publickey", "Allowed methods: ['publickey']"),
            ):
                with self.subTest(methods=methods):
                    attempts = []
                    with (
                        sftp_server(source, server_key, None, attempts, allowed_auths=methods) as port,
                        self.assertLogs(level="DEBUG") as logs,
                        self.assertRaisesRegex(RuntimeError, "authentication failed.*using password") as error,
                    ):
                        env = {
                            "SFTP_USERNAME": "artist",
                            "SFTP_PASSWORD": password,
                            "SFTP_KNOWN_HOSTS": (
                                f"[127.0.0.1]:{port} {server_key.get_name()} {server_key.get_base64()}"
                            ),
                        }
                        deploy(source, SftpConfig("127.0.0.1", port, "/site", False, ()), env)
                    self.assertEqual(["artist"], attempts)
                    self.assertIn(diagnostic, "\n".join(logs.output))
                    self.assertNotIn(password, "\n".join(logs.output) + str(error.exception))
                    if methods == "publickey":
                        self.assertIn("Server offered these methods: ['publickey']", str(error.exception))

    def test_upload_and_host_key_verification_on_loopback(self):
        import paramiko
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519

        def make_key():
            key = ed25519.Ed25519PrivateKey.generate()
            return key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.OpenSSH,
                                     serialization.NoEncryption()).decode("ascii")

        server_key = paramiko.Ed25519Key.from_private_key(StringIO(make_key()))
        login_key_text = make_key()
        login_key = paramiko.Ed25519Key.from_private_key(StringIO(login_key_text))
        wrong_key = paramiko.Ed25519Key.from_private_key(StringIO(make_key()))
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "build"
            source.mkdir()
            (source / "index.html").write_text("new home", encoding="utf-8")
            (source / "images").mkdir()
            (source / "images/banner.txt").write_text("banner", encoding="utf-8")
            (source / ".htaccess").write_text("new rules", encoding="utf-8")
            remote = root / "remote/site"
            remote.mkdir(parents=True)
            (remote / ".htaccess").write_text("old rules", encoding="utf-8")

            for auth in ("password", "key", "wrong host"):
                with self.subTest(auth=auth):
                    (remote / "old.html").write_text("obsolete", encoding="utf-8")
                    attempts = []
                    with sftp_server(remote.parent, server_key, login_key, attempts,
                                     expect_host_rejection=auth == "wrong host") as port:
                        supplied_key = wrong_key if auth == "wrong host" else server_key
                        env = {
                            "SFTP_USERNAME": "artist",
                            "SFTP_PASSWORD": "" if auth == "key" else "fixture-password",
                            "SFTP_PRIVATE_KEY": login_key_text.replace("\n", "\r\n") if auth == "key" else "",
                            "SFTP_KNOWN_HOSTS": (
                                f"[localhost]:{port},[127.0.0.1]:{port} "
                                f"{supplied_key.get_name()} {supplied_key.get_base64()}"
                            ),
                        }
                        config = SftpConfig("127.0.0.1", port, "/site", auth == "key", (".htaccess",))
                        if auth == "wrong host":
                            with self.assertRaisesRegex(RuntimeError, "host key verification failed"):
                                deploy(source, config, env)
                            self.assertEqual([], attempts)
                        else:
                            deploy(source, config, env)
                            self.assertEqual(["artist"], attempts)
                    self.assertEqual(auth != "key", (remote / "old.html").exists())
                    self.assertEqual("new home", (remote / "index.html").read_text(encoding="utf-8"))
                    self.assertEqual("banner", (remote / "images/banner.txt").read_text(encoding="utf-8"))
                    self.assertEqual("old rules", (remote / ".htaccess").read_text(encoding="utf-8"))
