import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from build.migration.toml_migration import PageMigrationReport, run_page_migration
from core import utils
from core.logging_config import configure_logging

logger = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate legacy comic_git config and page folders to TOML files."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Create planned TOML files. Without this flag, the script only reports what would change.",
    )
    parser.add_argument(
        "--main-only",
        action="store_true",
        help="Only migrate main comic config and pages; skip Extra Comics configured in comic_info.ini.",
    )
    parser.add_argument(
        "--delete-legacy",
        action="store_true",
        help="Delete legacy files when matching TOML files exist. This can be run after migration.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    args = parse_args(argv)
    utils.find_project_root()
    report = run_page_migration(
        write=args.write,
        include_extra_comics=not args.main_only,
        delete_legacy=args.delete_legacy,
    )
    print_report(report, write=args.write)
    return 0


def print_report(report: PageMigrationReport, write: bool) -> None:
    action = "Wrote" if write else "Would write"
    targets = report.written if write else report.planned
    comic_config_targets = report.comic_configs_written if write else report.comic_configs_planned
    for target in comic_config_targets:
        logger.info("%s %s", action, target.toml_info_path)
    for target in targets:
        logger.info("%s %s", action, target.toml_info_path)
    for skipped in report.skipped_comic_configs:
        logger.info("Skipped %s: %s", skipped.legacy_info_path, skipped.reason)
    for skipped in report.skipped:
        logger.info("Skipped %s: %s", skipped.page_path, skipped.reason)
    for deleted_path in report.deleted_legacy_files:
        logger.warning("Deleted legacy file %s", deleted_path)
    logger.info(
        "Summary: %s comic config %s, %s page %s, %s skipped, %s legacy files deleted",
        len(comic_config_targets),
        "written" if write else "planned",
        len(targets),
        "written" if write else "planned",
        len(report.skipped_comic_configs) + len(report.skipped),
        len(report.deleted_legacy_files),
    )
    if not write and (comic_config_targets or targets):
        logger.info("Dry run only. Re-run with --write to create these files.")


if __name__ == "__main__":
    sys.exit(main())
