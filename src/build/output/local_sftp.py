"""Native local SFTP transfer. The GitHub artifact runner stays dependency-free."""

from __future__ import annotations

import logging
from pathlib import Path, PurePosixPath
import stat
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from build.output.sftp import SftpConfig, deployment_credentials

if TYPE_CHECKING:
    from paramiko import SFTPClient


logger = logging.getLogger(__name__)


def require_paramiko():
    try:
        import paramiko
    except ImportError as error:
        raise RuntimeError(
            "Install the optional SFTP dependencies with "
            "python -m pip install -r comic_git_engine/requirements_sftp.txt."
        ) from error
    return paramiko


def local_entries(source: Path, excluded: set[PurePosixPath]) -> dict[PurePosixPath, int]:
    entries = {}
    pending = [source]
    while pending:
        for item in pending.pop().iterdir():
            path = PurePosixPath(item.relative_to(source).as_posix())
            if path in excluded:
                continue
            kind = stat.S_IFMT(item.lstat().st_mode)
            if kind not in (stat.S_IFDIR, stat.S_IFREG) or item.is_junction():
                raise ValueError(f"Unsupported local deployment path: {path}")
            entries[path] = kind
            if kind == stat.S_IFDIR:
                pending.append(item)
    return entries


def remote_entries(client: SFTPClient, local: dict[PurePosixPath, int],
                   excluded: set[PurePosixPath], clean: bool) -> dict[PurePosixPath, int]:
    entries = {}
    pending = [PurePosixPath(".")]
    while pending:
        parent = pending.pop()
        for item in client.listdir_attr(parent.as_posix()):
            if not item.filename or item.filename in (".", "..") or "/" in item.filename:
                raise ValueError(f"Invalid SFTP directory entry under {parent}")
            path = parent / item.filename
            if path in excluded:
                continue
            kind = stat.S_IFMT(item.st_mode or 0)
            entries[path] = kind
            if kind == stat.S_IFDIR and (clean or path in local):
                pending.append(path)
    return entries


def mirror_site(client: SFTPClient, source: Path, config: SftpConfig) -> None:
    excluded = {PurePosixPath(entry) for entry in config.exclusions}
    local = local_entries(source, excluded)
    # A symlink at the deployment root or in the remote tree must not redirect writes.
    if not stat.S_ISDIR(client.lstat(config.remote_dir).st_mode or 0):
        raise ValueError(f"SFTP destination must be an existing directory: {config.remote_dir}")
    client.chdir(config.remote_dir)
    remote = remote_entries(client, local, excluded, config.clean)

    for path in local.keys() & remote.keys():
        if local[path] != remote[path]:
            raise ValueError(f"SFTP destination has an incompatible file type at {path}")

    for path in sorted(local, key=lambda entry: (len(entry.parts), entry)):
        if local[path] == stat.S_IFDIR:
            if path not in remote:
                client.mkdir(path.as_posix())
        else:
            client.put(str(source.joinpath(*path.parts)), path.as_posix())

    if config.clean:
        # Keep ancestors of protected entries even when absent from the build.
        preserved = excluded | {path for path, kind in remote.items() if kind not in (stat.S_IFREG, stat.S_IFDIR)}
        preserved_dirs = {parent for path in preserved for parent in path.parents}
        for path in sorted(remote.keys() - local.keys(), key=lambda entry: (len(entry.parts), entry), reverse=True):
            if remote[path] == stat.S_IFREG:
                client.remove(path.as_posix())
            elif remote[path] == stat.S_IFDIR and path not in preserved_dirs:
                client.rmdir(path.as_posix())


def deploy(source: Path, config: SftpConfig, env: dict[str, str]) -> None:
    if not (source / "index.html").is_file():
        raise ValueError("Refusing SFTP deployment without a built index.html.")
    username, password, key, known_hosts = deployment_credentials(env)
    method = "password" if password else "public key"
    paramiko = require_paramiko()
    try:
        with TemporaryDirectory(prefix="comic-git-sftp-auth-") as auth_dir, paramiko.SSHClient() as ssh:
            hosts_file = Path(auth_dir) / "known_hosts"
            hosts_file.write_text(known_hosts.rstrip() + "\n", encoding="utf-8", newline="\n")
            ssh.load_host_keys(str(hosts_file))
            host = config.host if config.port == 22 else f"[{config.host}]:{config.port}"
            if not ssh.get_host_keys().lookup(host):
                raise ValueError(f"SFTP_KNOWN_HOSTS must contain a verified host key for {host}.")

            private_key = None
            if key:
                key_file = Path(auth_dir) / "identity"
                key_file.write_text(key.replace("\r\n", "\n").rstrip() + "\n",
                                    encoding="utf-8", newline="\n")
                key_file.chmod(0o600)
                private_key = paramiko.PKey.from_path(key_file)
                key_file.unlink()

            logger.debug("Connecting to %s:%d as %r using %s authentication",
                         config.host, config.port, username, method)
            ssh.connect(
                config.host, port=config.port, username=username, password=password or None,
                pkey=private_key, look_for_keys=False, allow_agent=False,
                timeout=20, banner_timeout=20, auth_timeout=20, channel_timeout=20,
            )
            with ssh.open_sftp() as client:
                client.get_channel().settimeout(30)
                mirror_site(client, source, config)
    except paramiko.BadHostKeyException:
        raise RuntimeError(f"SFTP host key verification failed for {config.host}.") from None
    except paramiko.BadAuthenticationType as error:
        raise RuntimeError(
            f"SFTP authentication failed for {config.host} using {method}. "
            f"Server offered these methods: {error.allowed_types!r}."
        ) from None
    except paramiko.AuthenticationException as error:
        logger.debug("SSH authentication exception: %s: %s", type(error).__name__, error)
        raise RuntimeError(f"SFTP authentication failed for {config.host} using {method}.") from None
    except paramiko.SSHException as error:
        raise RuntimeError(f"SFTP deployment failed: {error}") from None
