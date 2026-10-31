"""Contract checks for the reusable build and deployment workflow."""

import os
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from unittest import TestCase


WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/build_site.yaml"


def run_git(*args: str, cwd: Path, input_text: str | None = None) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, input=input_text, capture_output=True, text=True, check=True
    )
    return result.stdout


class TestActionsPerformanceWorkflow(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def sparse_script(self) -> str:
        match = re.search(
            r"- name: Sparse checkout caller repo.*?python - <<'PY'\n(?P<script>.*?)\n          PY",
            self.workflow,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        return textwrap.dedent(match.group("script"))

    def sparse_directory_script(self) -> str:
        block = self.workflow.split("- name: Sparse checkout caller repo", 1)[1].split(
            "- name: Read engine version", 1
        )[0]
        scripts = re.findall(r"python - <<'PY'\n(.*?)\n          PY", block, re.DOTALL)
        self.assertEqual(2, len(scripts))
        return textwrap.dedent(scripts[1])

    def sparse_patterns(self, value: str, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-c", self.sparse_script()],
            cwd=root,
            env={**os.environ, "CHECKOUT_EXCLUDE_PATHS": value, "RUNNER_TEMP": str(root)},
            capture_output=True,
            text=True,
        )

    def test_target_artifacts_and_permissions(self) -> None:
        build, pages = self.workflow.split("  deploy-github-pages:", 1)
        pages, neocities = pages.split("  deploy-neocities:", 1)
        self.assertEqual(1, build.count("uses: actions/upload-pages-artifact@"))
        self.assertIn("actions/upload-pages-artifact@7b1f4a764d45c48632c6b24a0339c27f5614fb0b", build)
        self.assertIn("if: ${{ inputs.DEPLOY_TARGET == 'github-pages' }}", build)
        self.assertIn("if: ${{ inputs.DEPLOY_TARGET == 'neocities' || inputs.DEPLOY_TARGET == 'sftp' }}", build)
        self.assertNotIn("actions/download-artifact@", pages)
        self.assertNotIn("actions/upload-pages-artifact@", pages)
        self.assertIn("uses: actions/configure-pages@", pages)
        self.assertIn("uses: actions/deploy-pages@", pages)
        self.assertIn("pages: write\n      id-token: write", pages)
        self.assertIn("name: site", neocities)
        self.assertIn("name: sftp-deployment", neocities)

    def test_output_and_retention_contract(self) -> None:
        self.assertEqual(3, self.workflow.count("retention-days: ${{ inputs.ARTIFACT_RETENTION_DAYS }}"))
        self.assertNotIn("inputs.OUTPUT_DIR || '.'", self.workflow)
        self.assertIn("OUTPUT_DIR: ${{ inputs.OUTPUT_DIR || 'build' }}", self.workflow)
        self.assertIn("if [[ ! -d \"$OUTPUT_DIR\" ]]", self.workflow)
        self.assertIn("ARTIFACT_RETENTION_DAYS must be an integer from 1 to 90", self.workflow)

    def test_sparse_input_rejects_patterns_and_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for value in ("../archive", "/archive", "archive/*", "archive/../secret", ".github", ".git/info", "archive\\old", "archive[1]", " archive", "archive ", "archive!old", "archive#old", "C:/archive", "\n"):
                with self.subTest(value=value):
                    result = self.sparse_patterns(value, root)
                    self.assertNotEqual(0, result.returncode, result.stderr)

    def test_sparse_patterns_preserve_other_files_and_avoid_excluded_blobs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            remote = root / "remote.git"
            checkout = root / "checkout"
            source.mkdir()
            checkout.mkdir()
            for name in (
                "README.md", ".github/workflows/site.yml", "custom_hook.json",
                "freezer_storage/old.bin", "archive/nested dir/old.bin",
                "archive/keep.txt", "your_content/transcripts/page.txt",
            ):
                file = source / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text(name, encoding="utf-8")
            run_git("init", cwd=source)
            run_git("add", ".", cwd=source)
            run_git("-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "fixture", cwd=source)
            excluded_blob = run_git("rev-parse", "HEAD:freezer_storage/old.bin", cwd=source).strip()
            run_git("init", "--bare", str(remote), cwd=root)
            run_git("config", "uploadpack.allowFilter", "true", cwd=remote)
            run_git("push", str(remote), "HEAD:refs/heads/main", cwd=source)

            result = self.sparse_patterns("freezer_storage\narchive/nested dir", root)
            self.assertEqual(0, result.returncode, result.stderr)
            patterns = (root / "comic-git-sparse-patterns").read_text(encoding="utf-8")
            run_git("init", cwd=checkout)
            run_git("remote", "add", "origin", remote.as_uri(), cwd=checkout)
            commit = run_git("rev-parse", "HEAD", cwd=source).strip()
            run_git("fetch", "--depth=1", "--filter=blob:none", "origin", commit, cwd=checkout)
            directory_check = subprocess.run(
                [sys.executable, "-c", self.sparse_directory_script()],
                cwd=checkout,
                env={**os.environ, "RUNNER_TEMP": str(root)},
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, directory_check.returncode, directory_check.stderr)
            run_git("sparse-checkout", "set", "--no-cone", "--stdin", cwd=checkout, input_text=patterns)
            run_git("checkout", "--detach", "FETCH_HEAD", cwd=checkout)

            self.assertFalse((checkout / "freezer_storage").exists())
            self.assertFalse((checkout / "archive/nested dir").exists())
            self.assertTrue((checkout / "archive/keep.txt").is_file())
            self.assertTrue((checkout / "README.md").is_file())
            self.assertTrue((checkout / ".github/workflows/site.yml").is_file())
            self.assertTrue((checkout / "custom_hook.json").is_file())
            self.assertTrue((checkout / "your_content/transcripts/page.txt").is_file())
            missing = run_git("rev-list", "--objects", "--missing=print", "HEAD", cwd=checkout)
            self.assertIn("?" + excluded_blob, missing)

            (root / "comic-git-sparse-patterns").write_text("/*\n!/README.md/\n", encoding="utf-8")
            invalid_check = subprocess.run(
                [sys.executable, "-c", self.sparse_directory_script()],
                cwd=checkout,
                env={**os.environ, "RUNNER_TEMP": str(root)},
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, invalid_check.returncode)
            self.assertIn("not a directory", invalid_check.stderr)
