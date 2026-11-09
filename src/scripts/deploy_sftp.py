"""Build and deploy a site over SFTP, or upload an existing build."""

import argparse
from getpass import getpass
import logging
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ENGINE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ENGINE_ROOT / "src"))

from build.output.local_sftp import deploy, require_paramiko
from build.output.sftp import SftpConfig, deployment_credentials


def build_and_deploy(project_root: Path, env: dict[str, str]) -> None:
    config = SftpConfig.from_environment(env)
    deployment_credentials(env)
    content = (project_root / 'your_content').resolve(strict=True)
    build_env = env.copy()
    # Workflow-only overrides can redirect output. Keep transfer credentials out
    # of the build process and its theme hooks.
    for name in ("INPUTS", "SECRETS", "SFTP_USERNAME", "SFTP_PASSWORD", "SFTP_PRIVATE_KEY", "SFTP_KNOWN_HOSTS"):
        build_env.pop(name, None)

    with tempfile.TemporaryDirectory(prefix="comic-git-sftp-") as directory:
        stage = Path(directory).resolve()
        if stage.is_relative_to(content) or stage.is_relative_to(ENGINE_ROOT):
            raise ValueError("The system temporary directory must be outside your_content and comic_git_engine.")
        output = stage / "build"
        subprocess.run(
            [sys.executable, '-B', str(ENGINE_ROOT / "src/build/build_site.py"),
             "--selective-copy", "--output-dir", str(output),
             "--hidden-paths", env.get("SFTP_HIDDEN_PATHS", "")],
            cwd=project_root, env=build_env, check=True,
        )
        deploy(output, config, env)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Build and deploy a local comic_git site over SFTP.",
        epilog="Set SFTP_HOST, SFTP_REMOTE_DIR, SFTP_USERNAME, and SFTP_KNOWN_HOSTS. "
               "Set SFTP_CLEAN=false to retain remote files absent from this build.",
    )
    parser.add_argument("--verbose", action="store_true", help="Show SSH negotiation and authentication diagnostics.")
    parser.add_argument("--upload-only", type=Path, metavar="DIRECTORY",
                        help="Upload this existing build without rebuilding.")
    args = parser.parse_args(argv)
    if args.verbose:
        logging.basicConfig(format="%(levelname)s %(name)s: %(message)s")
        logging.getLogger("build.output.local_sftp").setLevel(logging.DEBUG)
        logging.getLogger("paramiko.transport").setLevel(logging.DEBUG)
    require_paramiko()

    env = os.environ.copy()
    if (sys.stdin.isatty() and env.get("SFTP_USERNAME") and env.get("SFTP_KNOWN_HOSTS", "").strip()
            and not (env.get("SFTP_PASSWORD") or env.get("SFTP_PRIVATE_KEY"))):
        env["SFTP_PASSWORD"] = getpass("SFTP password: ")
    if args.upload_only is not None:
        deploy(args.upload_only, SftpConfig.from_environment(env), env)
        return

    from core.utils import find_project_root

    find_project_root()
    build_and_deploy(Path.cwd(), env)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError:
        raise SystemExit("Build failed. See the build error above.") from None
    except (ValueError, RuntimeError, OSError) as error:
        raise SystemExit(str(error)) from None
