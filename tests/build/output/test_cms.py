import os
import tempfile
from configparser import RawConfigParser
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from build.output.cms import (
    DECAP_CMS_URL,
    DECAP_CMS_VERSION,
    GENERATED_FILE_MARKER,
    CmsCollection,
    CmsReadinessError,
    CmsSettings,
    build_cms_collections,
    render_admin_config,
    render_admin_index,
    resolve_cms_settings,
    validate_cms_page_roots,
    write_cms_admin,
)


class TestRenderAdminIndex(TestCase):
    def test_renders_minimal_marked_noindex_page_with_exact_decap_pin(self):
        html = render_admin_index()

        self.assertIn(f"<!-- {GENERATED_FILE_MARKER} -->", html)
        self.assertIn('<meta name="robots" content="noindex, nofollow">', html)
        self.assertIn(f'<script src="{DECAP_CMS_URL}"></script>', html)
        self.assertIn(f"decap-cms@{DECAP_CMS_VERSION}/", html)
        self.assertNotIn("decap-cms@^", html)
        self.assertNotIn("{{ decap_cms_url }}", html)


class TestAdminConfig(TestCase):
    @staticmethod
    def make_info(name: str) -> RawConfigParser:
        comic_info = RawConfigParser()
        comic_info.add_section("Comic Info")
        comic_info.set("Comic Info", "Comic name", name)
        return comic_info

    def test_builds_main_first_and_deterministic_extra_collections(self):
        results = [
            SimpleNamespace(comic_folder="extras/Side Story/", comic_info=self.make_info("Side Story")),
            SimpleNamespace(comic_folder="bonus!", comic_info=self.make_info("Bonus")),
            SimpleNamespace(comic_folder="", comic_info=self.make_info("Main")),
        ]

        collections = build_cms_collections(results)

        self.assertEqual(
            [
                CmsCollection("main_comic_pages", "Main Comic Pages", "your_content/comics"),
                CmsCollection(
                    "extra_comic_1_extras_side_story",
                    "Side Story Pages",
                    "your_content/extras/Side Story/comics",
                ),
                CmsCollection("extra_comic_2_bonus", "Bonus Pages", "your_content/bonus!/comics"),
            ],
            collections,
        )

    def test_collection_ordinals_keep_duplicate_sanitized_names_unique(self):
        results = [
            SimpleNamespace(comic_folder="side-story", comic_info=self.make_info("One")),
            SimpleNamespace(comic_folder="side_story", comic_info=self.make_info("Two")),
            SimpleNamespace(comic_folder="", comic_info=self.make_info("Main")),
        ]

        collections = build_cms_collections(results)

        self.assertEqual("extra_comic_1_side_story", collections[1].name)
        self.assertEqual("extra_comic_2_side_story", collections[2].name)

    def test_requires_exactly_one_main_comic(self):
        with self.assertRaisesRegex(ValueError, "exactly one main comic"):
            build_cms_collections([])

    def test_rejects_unsafe_extra_comic_path(self):
        for comic_folder in ("/private", "../private"):
            with self.subTest(comic_folder=comic_folder):
                results = [
                    SimpleNamespace(
                        comic_folder=comic_folder,
                        comic_info=self.make_info("Private"),
                    ),
                    SimpleNamespace(comic_folder="", comic_info=self.make_info("Main")),
                ]

                with self.assertRaisesRegex(ValueError, "Invalid Extra Comic path"):
                    build_cms_collections(results)

    def test_renders_production_backend_and_complete_page_schema(self):
        settings = CmsSettings(
            enabled=True,
            repository="owner/comic",
            branch="cms",
            backend_base_url="https://auth.example.com/api",
            backend_auth_endpoint="auth",
            editorial_workflow=True,
        )

        config = render_admin_config(
            settings,
            [CmsCollection("main_comic_pages", "Main Comic Pages", "your_content/comics")],
        )

        self.assertIn(f"# {GENERATED_FILE_MARKER}", config)
        self.assertIn("  name: github", config)
        self.assertIn('  repo: "owner/comic"', config)
        self.assertIn('  branch: "cms"', config)
        self.assertIn('  base_url: "https://auth.example.com/api"', config)
        self.assertIn("publish_mode: editorial_workflow", config)
        self.assertIn('path: "{{slug}}/info"', config)
        self.assertIn('format: "toml"', config)
        self.assertIn("delete: false", config)
        self.assertIn('media_folder: ""', config)
        self.assertIn('name: "post_date", widget: "datetime"', config)
        self.assertIn('time_format: false', config)
        self.assertIn('name: "post_text", widget: "markdown", required: false', config)
        self.assertIn('name: "images"', config)
        self.assertIn('summary: "{{fields.filename}}"', config)
        self.assertIn('name: "filename", widget: "image", allow_multiple: false', config)
        self.assertEqual(2, config.count('label: "Hover text", name: "alt_text"'))
        self.assertEqual(2, config.count('label: "Screen reader text", name: "screen_reader_text"'))
        self.assertIn("editor:\n  preview: false", config)
        self.assertLess(
            config.index('name: "title", widget: "string"'),
            config.index('name: "images"'),
        )
        self.assertLess(
            config.index('name: "images"'),
            config.index('name: "post_date", widget: "datetime"'),
        )

    def test_renders_local_backend_without_remote_values(self):
        config = render_admin_config(
            CmsSettings(enabled=True, local_backend=True),
            [CmsCollection("main_comic_pages", "Main Comic Pages", "your_content/comics")],
        )

        self.assertIn("backend:\n  name: git-gateway\nlocal_backend: true", config)
        self.assertNotIn("repo:", config)
        self.assertNotIn("base_url:", config)
        self.assertNotIn("publish_mode:", config)

    def test_quotes_dynamic_yaml_values_against_injection(self):
        config = render_admin_config(
            CmsSettings(
                enabled=True,
                repository='owner/comic\"\nlocal_backend: true',
                backend_base_url="https://auth.example.com",
            ),
            [CmsCollection("main", 'Pages\"\nbackend:', "your_content/comics")],
        )

        self.assertIn('repo: "owner/comic\\\"\\nlocal_backend: true"', config)
        self.assertIn('label: "Pages\\\"\\nbackend:"', config)
        self.assertNotIn("\nlocal_backend: true\n", config)

    def test_rejects_disabled_or_collectionless_render(self):
        with self.assertRaisesRegex(ValueError, "CMS is disabled"):
            render_admin_config(CmsSettings(enabled=False), [])
        with self.assertRaisesRegex(ValueError, "without a comic collection"):
            render_admin_config(CmsSettings(enabled=True, local_backend=True), [])


class TestWriteCmsAdmin(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.host_root = self.temp_dir.name
        self.output_dir = os.path.join(self.host_root, "build")
        self.page_root = os.path.join(self.host_root, "your_content", "comics")
        os.makedirs(self.page_root)
        self.collection = CmsCollection("main", "Main Pages", "your_content/comics")

    def run_from_host_root(self, function):
        old_cwd = os.getcwd()
        try:
            os.chdir(self.host_root)
            function()
        finally:
            os.chdir(old_cwd)

    def test_writes_both_generated_files_and_overwrites_only_conflicts(self):
        admin_dir = os.path.join(self.output_dir, "admin")
        os.makedirs(admin_dir)
        index_path = os.path.join(admin_dir, "index.html")
        unrelated_path = os.path.join(admin_dir, "custom.css")
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("site_root index")
        with open(unrelated_path, "w", encoding="utf-8") as f:
            f.write("custom")

        with self.assertLogs("build.output.cms", level="WARNING") as logs:
            self.run_from_host_root(
                lambda: write_cms_admin(
                    CmsSettings(enabled=True, local_backend=True),
                    [self.collection],
                    self.output_dir,
                )
            )

        with open(index_path, encoding="utf-8") as f:
            self.assertIn(GENERATED_FILE_MARKER, f.read())
        with open(os.path.join(admin_dir, "config.yml"), encoding="utf-8") as f:
            self.assertIn(GENERATED_FILE_MARKER, f.read())
        with open(unrelated_path, encoding="utf-8") as f:
            self.assertEqual("custom", f.read())
        self.assertIn(index_path, "\n".join(logs.output))

    def test_validation_failure_writes_nothing(self):
        page_dir = os.path.join(self.page_root, "legacy")
        os.makedirs(page_dir)
        with open(os.path.join(page_dir, "info.ini"), "w", encoding="utf-8") as f:
            f.write("Post date = 09/05/2026")

        with self.assertRaises(CmsReadinessError):
            self.run_from_host_root(
                lambda: write_cms_admin(
                    CmsSettings(enabled=True, local_backend=True),
                    [self.collection],
                    self.output_dir,
                )
            )

        self.assertFalse(os.path.exists(os.path.join(self.output_dir, "admin")))

    def test_disabled_in_place_generation_removes_only_stale_generated_files(self):
        admin_dir = os.path.join(self.host_root, "admin")
        os.makedirs(admin_dir)
        generated_path = os.path.join(admin_dir, "config.yml")
        user_path = os.path.join(admin_dir, "custom.css")
        with open(generated_path, "w", encoding="utf-8") as f:
            f.write(f"# {GENERATED_FILE_MARKER}\n")
        with open(user_path, "w", encoding="utf-8") as f:
            f.write("custom")

        self.run_from_host_root(
            lambda: write_cms_admin(CmsSettings(enabled=False), [], "")
        )

        self.assertFalse(os.path.exists(generated_path))
        self.assertTrue(os.path.isfile(user_path))


class TestResolveCmsSettings(TestCase):
    @staticmethod
    def make_comic_info(**options) -> RawConfigParser:
        option_names = {
            "enabled": "Enabled",
            "repository": "Repository",
            "branch": "Branch",
            "backend_base_url": "Backend base URL",
            "backend_auth_endpoint": "Backend auth endpoint",
            "editorial_workflow": "Editorial workflow",
        }
        comic_info = RawConfigParser()
        comic_info.optionxform = str
        if options:
            comic_info.add_section("CMS")
            for option, value in options.items():
                comic_info.set("CMS", option_names[option], str(value))
        return comic_info

    def test_disabled_cms_returns_inert_defaults(self):
        comic_info = self.make_comic_info()

        settings = resolve_cms_settings(
            comic_info,
            source_is_toml=False,
            local_backend=True,
            environ={},
        )

        self.assertEqual(CmsSettings(enabled=False), settings)

    def test_enabled_cms_resolves_explicit_production_settings(self):
        comic_info = self.make_comic_info(
            enabled="true",
            repository="owner/comic",
            branch="cms",
            backend_base_url="https://auth.example.com",
            backend_auth_endpoint="oauth/auth",
            editorial_workflow="true",
        )

        settings = resolve_cms_settings(comic_info, source_is_toml=True, environ={})

        self.assertEqual(
            CmsSettings(
                enabled=True,
                repository="owner/comic",
                branch="cms",
                backend_base_url="https://auth.example.com",
                backend_auth_endpoint="oauth/auth",
                editorial_workflow=True,
            ),
            settings,
        )

    @patch.dict(os.environ, {"GITHUB_REPOSITORY": "environment/comic"}, clear=True)
    def test_repository_falls_back_to_github_environment(self):
        comic_info = self.make_comic_info(
            enabled="true",
            backend_base_url="https://auth.example.com",
        )

        settings = resolve_cms_settings(comic_info, source_is_toml=True)

        self.assertEqual("environment/comic", settings.repository)
        self.assertEqual("master", settings.branch)
        self.assertEqual("auth", settings.backend_auth_endpoint)

    def test_local_backend_needs_no_repository_or_oauth_url(self):
        comic_info = self.make_comic_info(enabled="true")

        settings = resolve_cms_settings(
            comic_info,
            source_is_toml=True,
            local_backend=True,
            environ={},
        )

        self.assertEqual(
            CmsSettings(enabled=True, local_backend=True),
            settings,
        )

    def test_rejects_ini_enablement(self):
        comic_info = self.make_comic_info(enabled="true")

        with self.assertRaisesRegex(ValueError, "comic_info.toml"):
            resolve_cms_settings(comic_info, source_is_toml=False, local_backend=True)

    def test_rejects_missing_repository_in_production(self):
        comic_info = self.make_comic_info(
            enabled="true",
            backend_base_url="https://auth.example.com",
        )

        with self.assertRaisesRegex(ValueError, "owner/repository"):
            resolve_cms_settings(comic_info, source_is_toml=True, environ={})

    def test_rejects_malformed_repository(self):
        comic_info = self.make_comic_info(
            enabled="true",
            repository="owner/nested/comic",
            backend_base_url="https://auth.example.com",
        )

        with self.assertRaisesRegex(ValueError, "owner/repository"):
            resolve_cms_settings(comic_info, source_is_toml=True, environ={})

    def test_rejects_blank_branch(self):
        comic_info = self.make_comic_info(enabled="true", branch=" ")

        with self.assertRaisesRegex(ValueError, "nonblank branch"):
            resolve_cms_settings(comic_info, source_is_toml=True, local_backend=True)

    def test_rejects_absolute_auth_endpoint(self):
        comic_info = self.make_comic_info(
            enabled="true",
            backend_auth_endpoint="https://auth.example.com/auth",
        )

        with self.assertRaisesRegex(ValueError, "relative path"):
            resolve_cms_settings(comic_info, source_is_toml=True, local_backend=True)

    def test_rejects_blank_auth_endpoint(self):
        comic_info = self.make_comic_info(
            enabled="true",
            backend_auth_endpoint=" ",
        )

        with self.assertRaisesRegex(ValueError, "relative path"):
            resolve_cms_settings(comic_info, source_is_toml=True, local_backend=True)

    def test_rejects_non_https_remote_backend(self):
        comic_info = self.make_comic_info(
            enabled="true",
            repository="owner/comic",
            backend_base_url="http://auth.example.com",
        )

        with self.assertRaisesRegex(ValueError, "absolute HTTPS URL"):
            resolve_cms_settings(comic_info, source_is_toml=True, environ={})

    def test_rejects_blank_or_qualified_remote_backend(self):
        for backend_base_url in ("", "https://auth.example.com?mode=unsafe"):
            with self.subTest(backend_base_url=backend_base_url):
                comic_info = self.make_comic_info(
                    enabled="true",
                    repository="owner/comic",
                    backend_base_url=backend_base_url,
                )

                with self.assertRaisesRegex(ValueError, "absolute HTTPS URL"):
                    resolve_cms_settings(comic_info, source_is_toml=True, environ={})

    def test_allows_http_loopback_backend(self):
        comic_info = self.make_comic_info(
            enabled="true",
            repository="owner/comic",
            backend_base_url="http://localhost:3000",
        )

        settings = resolve_cms_settings(comic_info, source_is_toml=True, environ={})

        self.assertEqual("http://localhost:3000", settings.backend_base_url)

    def test_rejects_editorial_workflow_with_local_backend(self):
        comic_info = self.make_comic_info(enabled="true", editorial_workflow="true")

        with self.assertRaisesRegex(ValueError, "does not support editorial workflow"):
            resolve_cms_settings(comic_info, source_is_toml=True, local_backend=True)

    def test_rejects_invalid_boolean(self):
        comic_info = self.make_comic_info(enabled="sometimes")

        with self.assertRaisesRegex(ValueError, "expected true or false"):
            resolve_cms_settings(comic_info, source_is_toml=True, local_backend=True)


class TestValidateCmsPageRoots(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.comics_root = os.path.join(self.temp_dir.name, "comics")
        os.makedirs(self.comics_root)

    def write_page_file(self, page_name: str, filename: str, text: str) -> str:
        page_dir = os.path.join(self.comics_root, page_name)
        os.makedirs(page_dir, exist_ok=True)
        path = os.path.join(page_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def test_accepts_compatible_image_and_text_only_pages(self):
        self.write_page_file(
            "image-page",
            "info.toml",
            """
post_date = 2026-09-04
title = "Image Page"
[[images]]
filename = "page.png"
""",
        )
        self.write_page_file(
            "text-page",
            "info.toml",
            """
post_date = "2026-09-05"
title = "Text Page"
post_text = "Hello"
[transcripts]
[social_media]
[extra]
""",
        )

        validate_cms_page_roots([self.comics_root])

    def test_missing_page_root_is_valid_for_an_empty_extra_comic(self):
        validate_cms_page_roots([os.path.join(self.temp_dir.name, "not-created-yet")])

    @patch("build.output.cms.os.scandir", side_effect=PermissionError("denied"))
    def test_reports_unreadable_page_root(self, _scandir):
        with self.assertRaises(CmsReadinessError) as raised:
            validate_cms_page_roots([self.comics_root])

        self.assertIn("could not inspect the comics folder (denied)", str(raised.exception))

    def test_rejects_non_iso_post_date(self):
        path = self.write_page_file(
            "invalid-date",
            "info.toml",
            'post_date = "September 5, 2026"\ntitle = "Invalid Date"',
        )

        with self.assertRaises(CmsReadinessError) as raised:
            validate_cms_page_roots([self.comics_root])

        self.assertIn(path, str(raised.exception))
        self.assertIn("fix the invalid page configuration", str(raised.exception))
        self.assertIn("ISO date or datetime", str(raised.exception))

    def test_aggregates_every_incompatible_page_and_remediation(self):
        ini_path = self.write_page_file("legacy", "info.ini", "Post date = 09/05/2026")
        missing_dir = os.path.join(self.comics_root, "missing")
        os.makedirs(missing_dir)
        invalid_path = self.write_page_file("invalid", "info.toml", "post_date = [")
        title_path = self.write_page_file("no-title", "info.toml", "post_date = 2026-09-05")
        timestamp_path = self.write_page_file(
            "timestamp",
            "info.toml",
            'post_date = 2026-09-05T10:30:00\ntitle = "Timestamp"',
        )
        tables_path = self.write_page_file(
            "tables",
            "info.toml",
            """
post_date = 2026-09-05
title = "Tables"
[transcripts]
English = "Words"
[social_media]
"og:title" = "Override"
[extra]
Mood = "tense"
""",
        )

        with self.assertRaises(CmsReadinessError) as raised:
            validate_cms_page_roots([self.comics_root])

        message = str(raised.exception)
        self.assertEqual(8, len(raised.exception.problems))
        self.assertIn(ini_path, message)
        self.assertIn("migrate this page", message)
        self.assertIn(missing_dir, message)
        self.assertIn("add an info.toml", message)
        self.assertIn(invalid_path, message)
        self.assertIn("fix the invalid page configuration", message)
        self.assertIn(title_path, message)
        self.assertIn("add a nonblank title", message)
        self.assertIn(timestamp_path, message)
        self.assertIn("date-only post_date", message)
        self.assertEqual(3, message.count(tables_path))
        self.assertIn("[transcripts]", message)
        self.assertIn("[social_media]", message)
        self.assertIn("[extra]", message)
