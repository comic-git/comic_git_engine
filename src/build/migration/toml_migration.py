import os
from dataclasses import dataclass, field
from glob import iglob
from typing import Callable

from configparser import RawConfigParser

from build.content import content_paths
from build.content.comic_config_sources import (
    CmsEnablementConfig,
    load_comic_config_from_toml,
    serialize_comic_config_to_toml,
)
from build.content.loaders import load_legacy_comic_info, load_legacy_extra_comic_info
from build.content.page_models import resolve_page_title
from build.content.page_sources import (
    load_legacy_page_source,
    load_page_source_from_toml,
    serialize_page_source_to_toml,
)
from core.stdlib_utils import str_to_list


@dataclass(frozen=True)
class PageMigrationTarget:
    comic_folder: str
    page_path: str
    legacy_info_path: str
    toml_info_path: str


@dataclass(frozen=True)
class SkippedPageMigration:
    comic_folder: str
    page_path: str
    reason: str


@dataclass(frozen=True)
class ComicConfigMigrationTarget:
    comic_folder: str
    legacy_info_path: str
    toml_info_path: str


@dataclass(frozen=True)
class SkippedComicConfigMigration:
    comic_folder: str
    legacy_info_path: str
    reason: str


@dataclass(frozen=True)
class MigrationFile:
    """One UTF-8 file the migration plan creates, addressed from the host repository root."""

    path: str
    content: str


@dataclass(frozen=True)
class PageMigrationPlan:
    """A write-free TOML migration result for one explicit comic_git repository root."""

    files: tuple[MigrationFile, ...]
    page_targets: tuple[PageMigrationTarget, ...]
    comic_config_targets: tuple[ComicConfigMigrationTarget, ...]
    skipped_pages: tuple[SkippedPageMigration, ...]
    skipped_comic_configs: tuple[SkippedComicConfigMigration, ...]


@dataclass
class PageMigrationReport:
    planned: list[PageMigrationTarget] = field(default_factory=list)
    written: list[PageMigrationTarget] = field(default_factory=list)
    skipped: list[SkippedPageMigration] = field(default_factory=list)
    comic_configs_planned: list[ComicConfigMigrationTarget] = field(default_factory=list)
    comic_configs_written: list[ComicConfigMigrationTarget] = field(default_factory=list)
    skipped_comic_configs: list[SkippedComicConfigMigration] = field(default_factory=list)
    deleted_legacy_files: list[str] = field(default_factory=list)


def plan_page_migration(
        repository_root: str,
        include_extra_comics: bool = True,
        cms_enablement: CmsEnablementConfig | None = None,
) -> PageMigrationPlan:
    """Build a deterministic legacy-to-TOML plan without changing the host repository."""
    repository_root = normalize_repository_root(repository_root)
    content_root = os.path.join(repository_root, "your_content")
    report = PageMigrationReport()
    comic_contexts = load_comic_contexts(content_root, include_extra_comics)
    comic_config_targets = discover_comic_config_migration_targets(
        content_root,
        include_extra_comics,
        comic_contexts[0][1],
        report,
    )
    page_targets: list[PageMigrationTarget] = []
    for comic_folder, _comic_info in comic_contexts:
        page_targets.extend(discover_page_migration_targets(content_root, comic_folder, report))

    comic_context_by_folder = dict(comic_contexts)
    files = [
        MigrationFile(
            repository_relative_path(repository_root, target.toml_info_path),
            serialize_comic_config_target(
                target,
                cms_enablement if target.comic_folder == "" else None,
            ),
        )
        for target in comic_config_targets
    ]
    for target in page_targets:
        files.append(
            MigrationFile(
                repository_relative_path(repository_root, target.toml_info_path),
                serialize_target(
                    target,
                    comic_context_by_folder[target.comic_folder],
                    content_root,
                    require_cms_title=cms_enablement is not None,
                ),
            )
        )
    return PageMigrationPlan(
        files=tuple(files),
        page_targets=tuple(page_targets),
        comic_config_targets=tuple(comic_config_targets),
        skipped_pages=tuple(report.skipped),
        skipped_comic_configs=tuple(report.skipped_comic_configs),
    )


def run_page_migration(
        write: bool = False,
        include_extra_comics: bool = True,
        delete_legacy: bool = False,
        repository_root: str | None = None,
) -> PageMigrationReport:
    """Plan or apply TOML migration while preserving the legacy CLI-facing report shape."""
    repository_root = normalize_repository_root(repository_root or os.getcwd())
    plan = plan_page_migration(repository_root, include_extra_comics)
    report = PageMigrationReport(
        skipped=list(plan.skipped_pages),
        skipped_comic_configs=list(plan.skipped_comic_configs),
    )
    if write:
        write_migration_files(repository_root, plan.files)
        report.written.extend(plan.page_targets)
        report.comic_configs_written.extend(plan.comic_config_targets)
    else:
        report.planned.extend(plan.page_targets)
        report.comic_configs_planned.extend(plan.comic_config_targets)
    if delete_legacy:
        comic_contexts = load_comic_contexts(
            os.path.join(repository_root, "your_content"),
            include_extra_comics,
        )
        validate_replacement_toml_files(repository_root, comic_contexts)
        for comic_folder, _comic_info in comic_contexts:
            delete_legacy_files_for_migrated_comic_configs(repository_root, comic_folder, report)
            delete_legacy_files_for_migrated_pages(repository_root, comic_folder, report)
    return report


def normalize_repository_root(repository_root: str) -> str:
    """Return an absolute host-repository root that has the required content directory."""
    normalized_root = os.path.abspath(repository_root)
    if not os.path.isdir(os.path.join(normalized_root, "your_content")):
        raise ValueError(
            "Expected repository_root to contain a your_content directory: "
            f"{normalize_filesystem_path(normalized_root)}"
        )
    return normalized_root


def repository_relative_path(repository_root: str, path: str) -> str:
    """Normalize a planned file path and reject writes outside its host repository."""
    relative_path = os.path.relpath(path, repository_root)
    if relative_path == os.pardir or relative_path.startswith(os.pardir + os.sep):
        raise ValueError(f"Migration path escapes repository root: {normalize_filesystem_path(path)}")
    return normalize_filesystem_path(relative_path)


def write_migration_files(repository_root: str, files: tuple[MigrationFile, ...]) -> None:
    """Apply a previously generated plan through exclusive UTF-8 file creation."""
    for migration_file in files:
        path = os.path.join(repository_root, migration_file.path)
        with open(path, "x", encoding="utf-8", newline="\n") as f:
            f.write(migration_file.content)


def load_comic_contexts(
        content_root: str,
        include_extra_comics: bool = True,
) -> list[tuple[str, RawConfigParser]]:
    legacy_path = os.path.join(content_root, "comic_info.ini")
    main_comic_info = load_legacy_comic_info(legacy_path)
    contexts = [("", main_comic_info)]
    if not include_extra_comics:
        return contexts
    for extra_comic in get_extra_comic_folders(main_comic_info):
        comic_folder = normalize_comic_folder(extra_comic)
        extra_legacy_path = os.path.join(content_root, comic_folder, "comic_info.ini")
        contexts.append((comic_folder, load_legacy_extra_comic_info(extra_legacy_path, main_comic_info)))
    return contexts


def normalize_comic_folder(comic_folder: str) -> str:
    stripped = comic_folder.strip("/")
    if not stripped:
        return ""
    return stripped + "/"


def get_extra_comic_folders(comic_info: RawConfigParser) -> list[str]:
    """Read extra-comic folders without importing the full site configuration graph."""
    return str_to_list(comic_info.get("Comic Settings", "Extra comics", fallback=""))


def discover_page_migration_targets(
        content_root: str,
        comic_folder: str,
        report: PageMigrationReport,
) -> list[PageMigrationTarget]:
    targets = []
    page_glob = os.path.join(content_root, comic_folder, "comics", "*/")
    for page_path in sorted(iglob(page_glob)):
        page_path = normalize_filesystem_path(os.path.normpath(page_path))
        toml_path, legacy_path = content_paths.get_page_info_candidates(page_path)
        toml_path = normalize_filesystem_path(toml_path)
        legacy_path = normalize_filesystem_path(legacy_path)
        if os.path.exists(toml_path):
            report.skipped.append(SkippedPageMigration(comic_folder, page_path, "info.toml already exists"))
            continue
        if not os.path.exists(legacy_path):
            report.skipped.append(SkippedPageMigration(comic_folder, page_path, "info.ini missing"))
            continue
        targets.append(PageMigrationTarget(comic_folder, page_path, legacy_path, toml_path))
    return targets


def discover_comic_config_migration_targets(
        content_root: str,
        include_extra_comics: bool,
        main_comic_info: RawConfigParser,
        report: PageMigrationReport,
) -> list[ComicConfigMigrationTarget]:
    targets = []
    add_comic_config_migration_target(
        "",
        os.path.join(content_root, "comic_info.ini"),
        os.path.join(content_root, "comic_info.toml"),
        targets,
        report,
    )
    if not include_extra_comics:
        return targets
    for extra_comic in get_extra_comic_folders(main_comic_info):
        comic_folder = normalize_comic_folder(extra_comic)
        add_comic_config_migration_target(
            comic_folder,
            os.path.join(content_root, comic_folder, "comic_info.ini"),
            os.path.join(content_root, comic_folder, "comic_info.toml"),
            targets,
            report,
        )
    return targets


def add_comic_config_migration_target(
        comic_folder: str,
        legacy_path: str,
        toml_path: str,
        targets: list[ComicConfigMigrationTarget],
        report: PageMigrationReport,
) -> None:
    legacy_path = normalize_filesystem_path(legacy_path)
    toml_path = normalize_filesystem_path(toml_path)
    if os.path.exists(toml_path):
        report.skipped_comic_configs.append(
            SkippedComicConfigMigration(comic_folder, legacy_path, "comic_info.toml already exists")
        )
        return
    if not os.path.exists(legacy_path):
        report.skipped_comic_configs.append(
            SkippedComicConfigMigration(comic_folder, legacy_path, "comic_info.ini missing")
        )
        return
    targets.append(ComicConfigMigrationTarget(comic_folder, legacy_path, toml_path))


def serialize_target(
        target: PageMigrationTarget,
        comic_info: RawConfigParser,
        content_root: str | None = None,
        *,
        require_cms_title: bool = False,
) -> str:
    page_source = load_legacy_page_source(
        target.page_path,
        target.comic_folder,
        comic_info,
        content_root=content_root,
    )
    if require_cms_title:
        page_source.title = resolve_page_title(
            page_source.title,
            [image.filename for image in page_source.images],
            os.path.basename(os.path.normpath(target.page_path)),
        )
    return serialize_page_source_to_toml(page_source)


def serialize_comic_config_target(
        target: ComicConfigMigrationTarget,
        cms_enablement: CmsEnablementConfig | None = None,
) -> str:
    comic_info = load_legacy_comic_info(target.legacy_info_path)
    return serialize_comic_config_to_toml(comic_info, cms_enablement)


def validate_replacement_toml_files(
        repository_root: str,
        comic_contexts: list[tuple[str, RawConfigParser]],
) -> None:
    content_root = os.path.join(repository_root, "your_content")
    for comic_folder, _comic_info in comic_contexts:
        comic_toml_path = os.path.join(content_root, comic_folder, "comic_info.toml")
        validate_replacement_toml_file(comic_toml_path, load_comic_config_from_toml)
        for page_path in sorted(iglob(os.path.join(content_root, comic_folder, "comics", "*/"))):
            page_toml_path, _legacy_path = content_paths.get_page_info_candidates(page_path)
            validate_replacement_toml_file(page_toml_path, load_page_source_from_toml)


def validate_replacement_toml_file(path: str, loader: Callable[[str], object]) -> None:
    if not os.path.exists(path):
        return
    try:
        loader(path)
    except Exception as e:
        normalized_path = normalize_filesystem_path(path)
        raise ValueError(
            f"Cannot delete legacy files because replacement TOML is invalid: {normalized_path}: {e}"
        ) from e


def delete_legacy_files_for_migrated_comic_configs(
        repository_root: str,
        comic_folder: str,
        report: PageMigrationReport,
) -> None:
    content_root = os.path.join(repository_root, "your_content")
    toml_path = os.path.join(content_root, comic_folder, "comic_info.toml")
    legacy_path = os.path.join(content_root, comic_folder, "comic_info.ini")
    if os.path.exists(toml_path) and os.path.exists(legacy_path):
        os.remove(legacy_path)
        report.deleted_legacy_files.append(repository_relative_path(repository_root, legacy_path))


def delete_legacy_files_for_migrated_pages(
        repository_root: str,
        comic_folder: str,
        report: PageMigrationReport,
) -> None:
    content_root = os.path.join(repository_root, "your_content")
    for page_path in sorted(iglob(os.path.join(content_root, comic_folder, "comics", "*/"))):
        page_path = os.path.normpath(page_path)
        toml_path, _ = content_paths.get_page_info_candidates(page_path)
        if not os.path.exists(toml_path):
            continue
        for legacy_path in get_page_legacy_file_paths(page_path):
            if os.path.exists(legacy_path):
                os.remove(legacy_path)
                report.deleted_legacy_files.append(repository_relative_path(repository_root, legacy_path))


def get_page_legacy_file_paths(page_path: str) -> list[str]:
    _, legacy_info_path = content_paths.get_page_info_candidates(page_path)
    paths = [
        legacy_info_path,
        os.path.join(page_path, "post.txt"),
        content_paths.get_page_social_media_path(page_path),
    ]
    for pattern in ("*.txt", "*.md"):
        for transcript_path in sorted(iglob(os.path.join(page_path, pattern))):
            if os.path.basename(transcript_path) == "post.txt":
                continue
            paths.append(transcript_path)
    return sorted(set(paths))


def normalize_filesystem_path(path: str) -> str:
    return path.replace("\\", "/")
