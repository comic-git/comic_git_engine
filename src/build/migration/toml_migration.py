import os
from dataclasses import dataclass, field
from glob import iglob

from configparser import RawConfigParser

from build.content import content_paths
from build.content.comic_config_sources import serialize_comic_config_to_toml
from build.content.loaders import load_legacy_comic_info, load_legacy_extra_comic_info
from build.content.page_sources import load_legacy_page_source, serialize_page_source_to_toml
from build.content.site_config import get_extra_comics_list


@dataclass
class PageMigrationTarget:
    comic_folder: str
    page_path: str
    legacy_info_path: str
    toml_info_path: str


@dataclass
class SkippedPageMigration:
    comic_folder: str
    page_path: str
    reason: str


@dataclass
class ComicConfigMigrationTarget:
    comic_folder: str
    legacy_info_path: str
    toml_info_path: str


@dataclass
class SkippedComicConfigMigration:
    comic_folder: str
    legacy_info_path: str
    reason: str


@dataclass
class PageMigrationReport:
    planned: list[PageMigrationTarget] = field(default_factory=list)
    written: list[PageMigrationTarget] = field(default_factory=list)
    skipped: list[SkippedPageMigration] = field(default_factory=list)
    comic_configs_planned: list[ComicConfigMigrationTarget] = field(default_factory=list)
    comic_configs_written: list[ComicConfigMigrationTarget] = field(default_factory=list)
    skipped_comic_configs: list[SkippedComicConfigMigration] = field(default_factory=list)
    deleted_legacy_files: list[str] = field(default_factory=list)


def run_page_migration(
        write: bool = False,
        include_extra_comics: bool = True,
        delete_legacy: bool = False,
) -> PageMigrationReport:
    report = PageMigrationReport()
    comic_contexts = load_comic_contexts(include_extra_comics)
    for target in discover_comic_config_migration_targets(include_extra_comics, comic_contexts[0][1], report):
        serialize_comic_config_target(target)
        if write:
            write_comic_config_target(target)
            report.comic_configs_written.append(target)
        else:
            report.comic_configs_planned.append(target)
    for comic_folder, comic_info in comic_contexts:
        for target in discover_page_migration_targets(comic_folder, report):
            serialize_target(target, comic_info)
            if write:
                write_target(target, comic_info)
                report.written.append(target)
            else:
                report.planned.append(target)
        if delete_legacy:
            delete_legacy_files_for_migrated_comic_configs(comic_folder, report)
            delete_legacy_files_for_migrated_pages(comic_folder, report)
    return report


def load_comic_contexts(include_extra_comics: bool = True) -> list[tuple[str, RawConfigParser]]:
    _, legacy_path = content_paths.get_main_comic_info_candidates()
    main_comic_info = load_legacy_comic_info(legacy_path)
    contexts = [("", main_comic_info)]
    if not include_extra_comics:
        return contexts
    for extra_comic in get_extra_comics_list(main_comic_info):
        comic_folder = normalize_comic_folder(extra_comic)
        _, extra_legacy_path = content_paths.get_extra_comic_info_candidates(comic_folder.strip("/"))
        contexts.append((comic_folder, load_legacy_extra_comic_info(extra_legacy_path, main_comic_info)))
    return contexts


def normalize_comic_folder(comic_folder: str) -> str:
    stripped = comic_folder.strip("/")
    if not stripped:
        return ""
    return stripped + "/"


def discover_page_migration_targets(
        comic_folder: str,
        report: PageMigrationReport,
) -> list[PageMigrationTarget]:
    targets = []
    for page_path in sorted(iglob(f"your_content/{comic_folder}comics/*/")):
        page_path = normalize_filesystem_path(page_path)
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
        include_extra_comics: bool,
        main_comic_info: RawConfigParser,
        report: PageMigrationReport,
) -> list[ComicConfigMigrationTarget]:
    targets = []
    toml_path, legacy_path = content_paths.get_main_comic_info_candidates()
    add_comic_config_migration_target("", legacy_path, toml_path, targets, report)
    if not include_extra_comics:
        return targets
    for extra_comic in get_extra_comics_list(main_comic_info):
        comic_folder = normalize_comic_folder(extra_comic)
        toml_path, legacy_path = content_paths.get_extra_comic_info_candidates(comic_folder.strip("/"))
        add_comic_config_migration_target(comic_folder, legacy_path, toml_path, targets, report)
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


def serialize_target(target: PageMigrationTarget, comic_info: RawConfigParser) -> str:
    page_source = load_legacy_page_source(target.page_path, target.comic_folder, comic_info)
    return serialize_page_source_to_toml(page_source)


def write_target(target: PageMigrationTarget, comic_info: RawConfigParser) -> None:
    toml_text = serialize_target(target, comic_info)
    with open(target.toml_info_path, "x", encoding="utf-8") as f:
        f.write(toml_text)


def serialize_comic_config_target(target: ComicConfigMigrationTarget) -> str:
    comic_info = load_legacy_comic_info(target.legacy_info_path)
    return serialize_comic_config_to_toml(comic_info)


def write_comic_config_target(target: ComicConfigMigrationTarget) -> None:
    toml_text = serialize_comic_config_target(target)
    with open(target.toml_info_path, "x", encoding="utf-8") as f:
        f.write(toml_text)


def delete_legacy_files_for_migrated_comic_configs(comic_folder: str, report: PageMigrationReport) -> None:
    toml_path, legacy_path = content_paths.get_main_comic_info_candidates() if not comic_folder else (
        content_paths.get_extra_comic_info_candidates(comic_folder.strip("/"))
    )
    if os.path.exists(toml_path) and os.path.exists(legacy_path):
        os.remove(legacy_path)
        report.deleted_legacy_files.append(normalize_filesystem_path(legacy_path))


def delete_legacy_files_for_migrated_pages(comic_folder: str, report: PageMigrationReport) -> None:
    for page_path in sorted(iglob(f"your_content/{comic_folder}comics/*/")):
        page_path = normalize_filesystem_path(page_path)
        toml_path, _ = content_paths.get_page_info_candidates(page_path)
        if not os.path.exists(toml_path):
            continue
        for legacy_path in get_page_legacy_file_paths(page_path):
            if os.path.exists(legacy_path):
                os.remove(legacy_path)
                report.deleted_legacy_files.append(normalize_filesystem_path(legacy_path))


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
    return sorted(set(normalize_filesystem_path(path) for path in paths))


def normalize_filesystem_path(path: str) -> str:
    return path.replace("\\", "/")
