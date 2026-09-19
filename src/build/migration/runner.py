"""Versioned JSON entry point for isolated CMS-enablement migration runners."""

import json
import sys
from typing import Any

from build.content.comic_config_sources import CmsEnablementConfig
from build.migration.toml_migration import PageMigrationPlan, plan_page_migration

PROTOCOL_VERSION = 1


def main() -> int:
    """Read one runner request from standard input and write one migration plan to standard output."""
    try:
        request = json.load(sys.stdin)
        plan = plan_page_migration(
            require_string(request, "repository_root"),
            cms_enablement=parse_cms_enablement(request.get("cms_enablement")),
        )
        json.dump(plan_to_data(plan), sys.stdout)
        sys.stdout.write("\n")
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"CMS migration runner rejected input: {error}", file=sys.stderr)
        return 2
    return 0


def parse_cms_enablement(value: object) -> CmsEnablementConfig:
    """Validate the fixed worker-to-engine CMS serialization input."""
    if not isinstance(value, dict):
        raise ValueError("cms_enablement must be an object")
    return CmsEnablementConfig(
        repository=require_string(value, "repository"),
        branch=require_string(value, "branch"),
        backend_base_url=require_string(value, "backend_base_url"),
        backend_auth_endpoint=require_string(value, "backend_auth_endpoint"),
        editorial_workflow=require_boolean(value, "editorial_workflow"),
    )


def require_string(data: object, key: str) -> str:
    """Return one nonblank protocol string without accepting coercible values."""
    if not isinstance(data, dict):
        raise ValueError("runner request must be an object")
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a nonblank string")
    return value


def require_boolean(data: object, key: str) -> bool:
    """Return one protocol boolean without accepting strings or integers."""
    if not isinstance(data, dict) or not isinstance(data.get(key), bool):
        raise ValueError(f"{key} must be a boolean")
    return data[key]


def plan_to_data(plan: PageMigrationPlan) -> dict[str, Any]:
    """Convert the immutable engine plan to the cross-process protocol payload."""
    return {
        "protocol_version": PROTOCOL_VERSION,
        "files": [
            {"path": migration_file.path, "content": migration_file.content}
            for migration_file in plan.files
        ],
        "skipped_pages": [
            {"path": skipped.page_path.replace("\\", "/"), "reason": skipped.reason}
            for skipped in plan.skipped_pages
        ],
        "skipped_comic_configs": [
            {"path": skipped.legacy_info_path.replace("\\", "/"), "reason": skipped.reason}
            for skipped in plan.skipped_comic_configs
        ],
    }


if __name__ == "__main__":
    sys.exit(main())
