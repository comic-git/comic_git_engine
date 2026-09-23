import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import TestCase


class TestMigrationRunnerContract(TestCase):
    """Exercise the worker-facing runner in an environment with only its declared dependencies."""

    def test_runner_creates_a_plan_with_only_declared_migration_dependencies(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository_root = Path(temporary_directory)
            page_directory = repository_root / "your_content" / "comics" / "first-page"
            page_directory.mkdir(parents=True)
            (repository_root / "your_content" / "comic_info.ini").write_text(
                "[Comic Info]\n"
                "Comic name = Test Comic\n"
                "Author = Test Author\n"
                "Description = Test Description\n\n"
                "[Comic Settings]\n"
                "Engine version = cms\n"
                "Date format = %B %d, %Y\n",
                encoding="utf-8",
            )
            (page_directory / "info.ini").write_text(
                "Post date = January 02, 2024\n",
                encoding="utf-8",
            )
            (page_directory / "comic.png").write_bytes(b"not-an-image")

            request = {
                "repository_root": str(repository_root),
                "cms_enablement": {
                    "repository": "comic-git/example",
                    "branch": "cms",
                    "backend_base_url": "https://worker.example.com",
                    "backend_auth_endpoint": "auth",
                    "editorial_workflow": False,
                },
            }
            environment = {
                "PYTHONIOENCODING": "utf-8",
                "PYTHONPATH": str(Path(__file__).resolve().parents[3] / "src"),
            }
            if os.name == "nt":
                environment["SYSTEMROOT"] = os.environ["SYSTEMROOT"]

            completed = subprocess.run(
                [sys.executable, "-m", "build.migration.runner"],
                input=json.dumps(request),
                text=True,
                capture_output=True,
                check=False,
                env=environment,
            )

        self.assertEqual(0, completed.returncode, completed.stderr)
        response = json.loads(completed.stdout)
        self.assertEqual(1, response["protocol_version"])
        self.assertEqual(
            [
                "your_content/comic_info.toml",
                "your_content/comics/first-page/info.toml",
            ],
            [migration_file["path"] for migration_file in response["files"]],
        )
        self.assertIn('title = "comic"', response["files"][1]["content"])
