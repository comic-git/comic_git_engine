<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: AI agents working on CI/CD pipelines, and developers.
     Purpose: Orient anyone working on the pipeline - where the configs live, what the key files are,
     and any non-obvious decisions that aren't visible in the config itself.
     Do NOT duplicate what is already in the config files. -->

# CI/CD

## Config Location

- Main workflow files:
  - [`.github/workflows/build_site.yaml`](../.github/workflows/build_site.yaml)
  - [`.github/workflows/main.yaml`](../.github/workflows/main.yaml)
- Shared templates / includes: none beyond the reusable workflow pattern in `build_site.yaml`

## Key Files

| File                                                                                            | Purpose                                                                                    |
|-------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| [`.github/workflows/build_site.yaml`](../.github/workflows/build_site.yaml)                     | Reusable workflow called by host `comic_git` repos to build and deploy static sites        |
| [`.github/workflows/main.yaml`](../.github/workflows/main.yaml)                                 | Maintainer workflow for version updates, branches, tags, and GitHub releases               |
| [`requirements.txt`](../requirements.txt)                                                       | Core runtime Python dependencies installed during build workflow execution                 |
| [`requirements_migration.txt`](../requirements_migration.txt)                                   | Migration-only Python dependencies for local one-off conversion tooling                    |
| [`src/scripts/make_requirements_hooks_file.py`](../src/scripts/make_requirements_hooks_file.py) | Generates optional hook dependency requirements during the build workflow                  |
| [`requirements_hooks.txt`](../requirements_hooks.txt)                                           | Generated file used only when theme hook dependencies are needed during workflow execution |

## Non-Obvious Decisions

- `build_site.yaml` is part of the product surface, not just internal CI. Host repos call it remotely via `uses: comic-git/comic_git_engine/.github/workflows/build_site.yaml@...`, so changes to that workflow affect end-user builds directly.
- Runtime dependency changes are CI/CD-sensitive because every end-user build installs them. Treat dependency additions as product-impacting changes, not just local tooling changes.
- Migration-only dependencies belong in `requirements_migration.txt`, not `requirements.txt`, unless they become required for normal site builds.
- `main.yaml` updates version branches and tags for the engine repo, but reusable workflow consumers may also be following the separate `v1` tag. Release and rollback thinking should include both version branches and workflow tag consumers.

## Version Source Of Truth

For `1.1`, the engine version source of truth is:

- [`src/build/site_builder.py`](../src/build/site_builder.py)
  - the `VERSION = "..."` constant
- [`.github/workflows/build_site.yaml`](../.github/workflows/build_site.yaml)
  - the `DEFAULT_ENGINE_VERSION = "..."` fallback used when host config omits an engine version

The maintainer release workflow in [`.github/workflows/main.yaml`](../.github/workflows/main.yaml) updates the `VERSION` constant and the reusable workflow fallback before it creates version branches, tags, and the GitHub release.

When checking release readiness, verify these three things together:

- `main.yaml` still edits `src/build/site_builder.py`
- `main.yaml` still updates `DEFAULT_ENGINE_VERSION` in `build_site.yaml` to the release major/minor value
- the requested release version matches the updated `VERSION` constant
- the created branches and tags match that same version

## Jobs Requiring Care

- [`.github/workflows/build_site.yaml`](../.github/workflows/build_site.yaml)
  - This is the end-user integration surface.
  - Changes here can break builds across many host repos at once.
- [`.github/workflows/main.yaml`](../.github/workflows/main.yaml)
  - This controls version bumps, release tags, and release artifacts for `comic_git_engine`.
  - Mistakes here can create confusing or incorrect release state.
- Dependency installation steps in `build_site.yaml`
  - These affect every automated end-user build.
  - Runtime dependency changes should be reviewed very carefully.
