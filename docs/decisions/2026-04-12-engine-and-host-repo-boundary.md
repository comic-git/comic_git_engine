<!-- ai-agent-toolkit:managed version="1.0.0" -->

# Engine and host repo boundary

| Field             | Value      |
|-------------------|------------|
| **Date**          | 2026-04-12 |
| **Status**        | `active`   |
| **Supersedes**    |            |
| **Superseded by** |            |

## Context

`comic_git_engine` is not the product users edit directly. Users create a repo from `comic_git`, keep their own data there, and let GitHub Actions load `comic_git_engine` at build time.

This split exists to keep as much behavior as possible centralized and updatable without asking non-technical users to copy code or modify workflow logic.

The workflow entry point is especially sensitive. Most user-controlled engine version changes happen through `comic_info.ini`. Changing workflow wiring would instead require users to edit GitHub Actions YAML, which is much less accessible.

## Decision

Keep `comic_git_engine` as the central implementation repo and keep host `comic_git` repos thin.

- Build logic, default templates, default CSS/JS, and reusable workflow behavior should live in `comic_git_engine` where possible.
- Host repos should primarily contain user data, user-owned customization files, and the minimum scaffolding needed to call the engine.
- Development and manual testing should happen through a host repo such as `comic_git_dev`, because that is the real runtime environment.
- Treat `.github/workflows/build_site.yaml` as part of the product surface. Do not change it casually.

## Consequences

This makes it much easier to roll out fixes and improvements to users without asking them to copy code around.

It also means:

- `comic_git_engine` should not be treated like a standalone app or service
- local development needs a host repo context
- workflow-level changes need extra caution because they are harder for users to adopt than normal engine version updates

## Files Affected

- `scripts/build_site.py`
- `scripts/*.py`
- `.github/workflows/build_site.yaml`
- `.github/workflows/main.yaml`
- `README.md`
- `docs/dev_setup.md`
- `docs/architecture.md`
- `docs/infrastructure.md`
- `docs/cicd.md`
