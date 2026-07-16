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
        description="Migrate legacy comic page folders to page-level info.toml files."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Create planned info.toml files. Without this flag, the script only reports what would change.",
    )
    parser.add_argument(
        "--main-only",
        action="store_true",
        help="Only migrate main comic pages; skip Extra Comics configured in comic_info.ini.",
    )
    parser.add_argument(
        "--delete-legacy",
        action="store_true",
        help="Delete page-scoped legacy files for pages with info.toml. This can be run after migration.",
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
    for target in targets:
        logger.info("%s %s", action, target.toml_info_path)
    for skipped in report.skipped:
        logger.info("Skipped %s: %s", skipped.page_path, skipped.reason)
    for deleted_path in report.deleted_legacy_files:
        logger.warning("Deleted legacy file %s", deleted_path)
    logger.info(
        "Summary: %s %s, %s skipped, %s legacy files deleted",
        len(targets),
        "written" if write else "planned",
        len(report.skipped),
        len(report.deleted_legacy_files),
    )
    if not write and targets:
        logger.info("Dry run only. Re-run with --write to create these files.")


if __name__ == "__main__":
    sys.exit(main())
