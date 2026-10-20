"""Prepare SFTP deployment files at build time and run them with deploy-time secrets.

This module uses only the standard library so a copy can run independently in
the deployment job, without checking out or installing the engine again.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
from urllib.parse import quote


def lftp_quote(value: str) -> str:
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError("SFTP paths and connection settings must not contain control characters.")
    # lftp treats dollar signs and backticks literally, unlike Bash.
    return '"' + re.sub(r'([\\"])', r'\\\1', value) + '"'


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
        lftp_quote(remote)
        exclusions = []
        for line in env.get("SFTP_EXCLUDE_PATHS", "").splitlines():
            entry = line.strip().rstrip("/")
            if not entry:
                continue
            if any(part in ("", ".", "..") for part in entry.split("/")) or "\\" in entry:
                raise ValueError("SFTP_EXCLUDE_PATHS must contain exact relative paths without traversal.")
            lftp_quote(entry)
            exclusions.append(entry)
        return cls(host, int(port), remote, clean == "true", tuple(exclusions))


def validate_deployment_directory(output_dir: str, deployment_dir: str) -> None:
    source = Path(output_dir).resolve()
    destination = Path(deployment_dir).resolve()
    project = Path.cwd().resolve()
    if (source == destination or source in destination.parents or destination in source.parents
            or destination == project or destination in project.parents
            or any(parent.resolve() == destination or parent.resolve() in destination.parents
                   for parent in (project / "your_content", project / "comic_git_engine"))):
        raise ValueError("SFTP deployment files must be separate from the site output and source directories.")


def deployment_commands(config: SftpConfig) -> str:
    """Generate a relocatable script; its local working directory is the built site."""
    # Artifact timestamps cannot reliably detect same-size edits or rollbacks.
    mirror = ["mirror", "--reverse", "--no-perms", "--no-symlinks", "--scan-all-first", "--transfer-all"]
    if config.clean:
        mirror.append("--delete")
    for entry in config.exclusions:
        mirror += ["--exclude", lftp_quote("^" + re.escape(entry) + "(/|$)")]
    mirror += ["--", ".", "."]
    # Fail on a missing destination rather than creating a misspelled directory.
    return "\n".join(["cd " + lftp_quote(config.remote_dir), " ".join(mirror), "bye", ""])


def write_deployment_files(output_dir: str, deployment_dir: str, config: SftpConfig) -> None:
    validate_deployment_directory(output_dir, deployment_dir)
    if not (Path(output_dir) / "index.html").is_file():
        raise ValueError("Refusing SFTP deployment without a built index.html.")
    destination = Path(deployment_dir)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "deploy.lftp").write_text(deployment_commands(config), encoding="utf-8")
    (destination / "connection.json").write_text(
        json.dumps({"host": config.host, "port": config.port}) + "\n", encoding="utf-8")
    shutil.copyfile(__file__, destination / "deploy.py")


def deploy(deployment_dir: str, output_dir: str, env) -> None:
    """Supply credentials only at execution time, then run the prepared transfer."""
    source = Path(output_dir).resolve()
    if not (source / "index.html").is_file():
        raise ValueError("Refusing SFTP deployment without a built index.html.")
    username = env.get("SFTP_USERNAME", "")
    password = env.get("SFTP_PASSWORD", "")
    key = env.get("SFTP_PRIVATE_KEY", "")
    known_hosts = env.get("SFTP_KNOWN_HOSTS", "")
    if not username or not known_hosts.strip() or bool(password) == bool(key):
        raise ValueError("Set SFTP_USERNAME, SFTP_KNOWN_HOSTS, and exactly one of SFTP_PASSWORD or SFTP_PRIVATE_KEY.")
    bundle = Path(deployment_dir)
    connection = json.loads((bundle / "connection.json").read_text(encoding="utf-8"))
    script = (bundle / "deploy.lftp").read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="sftp-auth-", dir=env.get("RUNNER_TEMP")) as auth_dir:
        auth = Path(auth_dir)
        hosts_file = auth / "known_hosts"
        hosts_file.write_text(known_hosts.rstrip() + "\n", encoding="utf-8")
        hosts_file.chmod(0o600)
        ssh = ["ssh", "-a", "-x", "-F", "/dev/null", "-o", "StrictHostKeyChecking=yes",
               "-o", f"UserKnownHostsFile={hosts_file}", "-o", "GlobalKnownHostsFile=/dev/null",
               "-o", "ConnectTimeout=20", "-o", "NumberOfPasswordPrompts=1"]
        if key:
            key_file = auth / "identity"
            # Secrets pasted or piped from Windows may contain CRLF. OpenSSH
            # expects LF, including the terminating newline, on every platform.
            key_file.write_bytes((key.replace("\r\n", "\n").rstrip() + "\n").encode("utf-8"))
            key_file.chmod(0o600)
            ssh += ["-i", str(key_file), "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes"]
        else:
            ssh += ["-o", "PubkeyAuthentication=no", "-o", "PreferredAuthentications=password,keyboard-interactive"]
        url = f'sftp://{quote(username, safe="")}@{connection["host"]}:{connection["port"]}'
        commands = [
            "set cmd:fail-exit yes", "set cmd:move-background no",
            "set net:max-retries 2", "set net:timeout 20", "set sftp:auto-confirm no",
            "set sftp:connect-program " + lftp_quote(shlex.join(ssh)),
            "open --env-password " + lftp_quote(url),
            script,
        ]
        client_env = dict(env)
        client_env["LFTP_PASSWORD"] = password
        result = subprocess.run(["lftp", "--norc"], input="\n".join(commands), text=True,
                                cwd=source, env=client_env)
        if result.returncode:
            raise RuntimeError("SFTP deployment failed; inspect the client error above.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy a prepared comic_git SFTP build")
    parser.add_argument("--output-dir", required=True, help="Downloaded public site directory")
    args = parser.parse_args()
    try:
        deploy(str(Path(__file__).resolve().parent), args.output_dir, os.environ)
    except (ValueError, RuntimeError, OSError) as error:
        raise SystemExit(str(error)) from None
