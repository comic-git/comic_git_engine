"""Configuration shared by local and hosted SFTP deployment."""

from dataclasses import dataclass
import re


def validate_path_characters(value: str) -> None:
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError("SFTP paths must not contain control characters.")


@dataclass(frozen=True)
class SftpConfig:
    host: str
    port: int
    remote_dir: str
    clean: bool
    exclusions: tuple[str, ...]

    @classmethod
    def from_environment(cls, env) -> SftpConfig:
        host = env.get("SFTP_HOST", "")
        port = env.get("SFTP_PORT", "22")
        remote = env.get("SFTP_REMOTE_DIR", "").rstrip("/")
        clean = env.get("SFTP_CLEAN", "true")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]*", host):
            raise ValueError("SFTP_HOST must be a hostname or IPv4 address, without a protocol or path.")
        if not port.isdecimal() or not 1 <= int(port) <= 65535:
            raise ValueError("SFTP_PORT must be an integer between 1 and 65535.")
        if clean not in ("true", "false"):
            raise ValueError("SFTP_CLEAN must be true or false.")
        parts = remote.lstrip("/").split("/")
        if (any(part in ("", ".", "..") for part in parts) or remote.startswith(("~", "//"))
                or "\\" in remote or ":" in remote
                or remote in ("/home", "/root", "/var", "/var/www", "/srv", "/usr", "/etc")
                or (remote.startswith("/home/") and len(parts) < 3)):
            raise ValueError("SFTP_REMOTE_DIR must name a website directory, not a root/home directory or traversal path.")
        if not remote.startswith("/"):
            remote = "./" + remote
        validate_path_characters(remote)
        exclusions = []
        for line in env.get("SFTP_EXCLUDE_PATHS", "").splitlines():
            entry = line.strip().rstrip("/")
            if not entry:
                continue
            if any(part in ("", ".", "..") for part in entry.split("/")) or "\\" in entry:
                raise ValueError("SFTP_EXCLUDE_PATHS must contain exact relative paths without traversal.")
            validate_path_characters(entry)
            exclusions.append(entry)
        return cls(host, int(port), remote, clean == "true", tuple(exclusions))


def deployment_credentials(env) -> tuple[str, str, str, str]:
    username = env.get("SFTP_USERNAME", "")
    password = env.get("SFTP_PASSWORD", "")
    key = env.get("SFTP_PRIVATE_KEY", "")
    known_hosts = env.get("SFTP_KNOWN_HOSTS", "")
    if not username or not known_hosts.strip() or bool(password) == bool(key):
        raise ValueError("Set SFTP_USERNAME, SFTP_KNOWN_HOSTS, and exactly one of SFTP_PASSWORD or SFTP_PRIVATE_KEY.")
    return username, password, key, known_hosts
