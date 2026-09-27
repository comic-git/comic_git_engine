"""CMS editing checks shared by site output and the stdlib-only migration runner."""

import os
import tomllib
from collections.abc import Mapping

from build.content import content_paths
from build.content.comic_config_sources import comic_config_data_to_legacy_parser
from build.content.page_sources import load_page_source_from_toml, parse_iso_post_date


class CmsReadinessError(ValueError):
    def __init__(self, problems: list[str]):
        self.problems = tuple(problems)
        super().__init__(
            "The CMS cannot safely edit the current site yet:\n- " + "\n- ".join(problems)
        )


def validate_cms_inputs(main_config_path: str, page_roots: list[str]) -> None:
    problems = [
        *_get_main_config_readiness_problems(main_config_path),
        *_get_page_roots_readiness_problems(page_roots),
    ]
    if problems:
        raise CmsReadinessError(problems)


def validate_cms_main_config(path: str = "your_content/comic_info.toml") -> None:
    problems = _get_main_config_readiness_problems(path)
    if problems:
        raise CmsReadinessError(problems)


def _get_main_config_readiness_problems(path: str) -> list[str]:
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        comic_config_data_to_legacy_parser(data)
    except (OSError, ValueError, KeyError) as e:
        return [f"{path}: fix the invalid comic_info.toml configuration ({e})."]

    problems = []
    legacy = data.get("legacy")
    if isinstance(legacy, dict):
        for section_name, values in legacy.items():
            if values:
                problems.append(
                    f"{path}: migrate or remove legacy.{section_name}; "
                    "the Comic Settings form cannot preserve arbitrary legacy values."
                )
    return problems


def validate_cms_page_roots(page_roots: list[str]) -> None:
    problems = _get_page_roots_readiness_problems(page_roots)
    if problems:
        raise CmsReadinessError(problems)


def _get_page_roots_readiness_problems(page_roots: list[str]) -> list[str]:
    problems = []
    for page_root in page_roots:
        try:
            entries = sorted(os.scandir(page_root), key=lambda entry: entry.name.casefold())
        except FileNotFoundError:
            continue
        except OSError as e:
            problems.append(f"{page_root}: could not inspect the comics folder ({e}).")
            continue
        for entry in entries:
            if entry.is_dir():
                problems.extend(_get_page_readiness_problems(entry.path))
    return problems


def _get_page_readiness_problems(page_path: str) -> list[str]:
    toml_path, ini_path = content_paths.get_page_info_candidates(page_path)
    if not os.path.isfile(toml_path):
        if os.path.isfile(ini_path):
            return [f"{ini_path}: migrate this page from info.ini to info.toml."]
        return [f"{page_path}: add an info.toml file before managing this folder with the CMS."]

    try:
        with open(toml_path, "rb") as f:
            raw_page_data = tomllib.load(f)
        source = load_page_source_from_toml(toml_path)
    except (OSError, ValueError, KeyError) as e:
        return [f"{toml_path}: fix the invalid page configuration ({e})."]

    problems = []
    if source.title is None or not source.title.strip():
        problems.append(f"{toml_path}: add a nonblank title for CMS editing.")

    raw_post_date = raw_page_data.get("post_date")
    if not isinstance(raw_post_date, str):
        problems.append(
            f'{toml_path}: put quotes around post_date, such as "2026-09-05"; '
            "CMS-managed dates must be ISO strings."
        )
    else:
        try:
            parsed_post_date = parse_iso_post_date(source.post_date)
        except ValueError:
            parsed_post_date = None
        if parsed_post_date is None or hasattr(parsed_post_date, "hour"):
            problems.append(
                f'{toml_path}: use a date-only post_date such as "2026-09-05"; '
                "timestamp editing is not supported yet."
            )

    unsupported_values = {"extra": source.extra}
    for table_name, value in unsupported_values.items():
        if value:
            problems.append(
                f"{toml_path}: remove or manually manage the nonempty [{table_name}] table; "
                "the first CMS editor cannot preserve it yet."
            )
    for table_name, value in {
        "transcripts": source.transcripts,
        "social_media": source.social_media,
    }.items():
        if value and not _is_editable_string_map(value):
            problems.append(
                f"{toml_path}: use nonblank string keys and string values in [{table_name}]; "
                "the CMS editor supports only simple key/value maps."
            )
    return problems


def _is_editable_string_map(value: Mapping[str, object]) -> bool:
    return all(
        isinstance(key, str) and bool(key.strip()) and isinstance(metadata, str)
        for key, metadata in value.items()
    )
