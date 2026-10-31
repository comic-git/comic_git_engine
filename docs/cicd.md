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
| `requirements_hooks.txt`                                                                        | Generated file used only when theme hook dependencies are needed during workflow execution |

## Non-Obvious Decisions

- `build_site.yaml` is part of the product surface, not just internal CI. Host repos call it remotely via `uses: comic-git/comic_git_engine/.github/workflows/build_site.yaml@...`, so changes to that workflow affect end-user builds directly.
- The build uploads one target-specific site artifact. GitHub Pages receives its validated `github-pages` artifact directly from the build job; Neocities and SFTP download the generic `site` artifact into the resolved `OUTPUT_DIR`. The separate deployment jobs and their environment gates remain in place.
- The reusable workflow resolves an omitted or blank `OUTPUT_DIR` to `build` in both the builder and artifact steps. It rejects the checkout root as output. This differs from the local Python builder's explicit blank-value in-place mode, which is unsuitable for publishing an artifact from the whole checkout.
- The pinned Pages uploader excludes files and directories whose names begin with `.`, matching the generic uploader's Pages/Neocities behavior. For SFTP, the build script filters hidden paths in its output and the generic artifact uploader preserves that directory as produced; see [SFTP deployment](features/sftp/). Underscore-prefixed generated files such as `_thumbnail.jpg` are ordinary files and are included.
- `ARTIFACT_RETENTION_DAYS` defaults to one day for the Pages, generic site, and SFTP helper artifacts. The workflow accepts integers from 1 to 90; repository or organization settings can impose a shorter maximum. A deployment-only retry needs the artifact to remain available, so choose a longer value when environment approval may be delayed.
- `CHECKOUT_EXCLUDE_PATHS` is an opt-in newline-separated list of exact caller-repository directories. With no exclusions the workflow uses the normal shallow checkout. With exclusions it performs a shallow blob-filtered fetch, verifies each named path is a directory, installs non-cone sparse rules before checkout, and leaves omitted blobs unfetched. The input rejects patterns, traversal, absolute paths, and `.git`/`.github` exclusions. Callers must keep all content, transcript, and custom-hook inputs needed by their build. The engine checkout is independent of these rules.
- Runtime dependency changes are CI/CD-sensitive because every end-user build installs them. Treat dependency additions as product-impacting changes, not just local tooling changes.
- Migration-only dependencies belong in `requirements_migration.txt`, not `requirements.txt`, unless they become required for normal site builds.
- The build checks out the engine directly into `comic_git_engine/` using the configured version, with TOML taking precedence over legacy INI and `1.1` as the fallback. Caller submodules are not initialized, so a committed engine submodule does not override that version or require remote-tracking branches during CI.
- Host repos make two independent version choices: the reusable workflow revision in `uses: .../build_site.yaml@...` and the engine revision in their comic configuration. Changing one does not change the other.
- `v1` is frozen at the 1.0 reusable-workflow contract. Major tags are managed manually and are never created, moved, or deleted by `main.yaml`.

## SFTP deployment

`DEPLOY_TARGET: sftp` uses the shared build and a separate deployment artifact.
The build owns publication policy and generates the deployment files; the
deployment job installs `lftp` and runs them with credentials supplied only at
deployment time. See [SFTP deployment](features/sftp/) for directory ownership,
hidden-file, authentication, and failure rules.

## Version Source Of Truth

For `1.1`, the engine version source of truth is:

- [`src/build/site_builder.py`](../src/build/site_builder.py)
  - the `VERSION = "..."` constant
- [`.github/workflows/build_site.yaml`](../.github/workflows/build_site.yaml)
  - the `DEFAULT_ENGINE_VERSION = "..."` fallback used when host config omits an engine version

The maintainer release workflow in [`.github/workflows/main.yaml`](../.github/workflows/main.yaml) updates the `VERSION` constant and the reusable workflow fallback before it creates version branches, tags, and the GitHub release.

For a release such as `1.1.0`, the workflow manages these references:

| Reference | Stability | Purpose                                                                |
|-----------|-----------|------------------------------------------------------------------------|
| `latest`  | Moving    | Most recent engine release                                             |
| `1.1`     | Moving    | Engine selector that receives compatible 1.1 patch releases            |
| `v1.1`    | Moving    | Reusable-workflow selector that receives compatible 1.1 patch releases |
| `1.1.0`   | Immutable | Exact engine branch                                                    |
| `v1.1.0`  | Immutable | Exact reusable-workflow tag and GitHub Release tag                     |

The normal host defaults are workflow `@v1.1` and engine version `1.1`. A host that requires an exactly reproducible build must pin both selectors independently to `@v1.1.0` and `1.1.0`.

When checking release readiness, verify these checks together:

- `main.yaml` still edits `src/build/site_builder.py`
- `main.yaml` still updates `DEFAULT_ENGINE_VERSION` in `build_site.yaml` to the release major/minor value
- the requested release version matches the updated `VERSION` constant
- the created branches and tags match that same version

## Release Workflow Safety and Recovery

Dispatch `main.yaml` from `master` with a canonical numeric `X.Y.Z` version. Its validation phase rejects non-`master` dispatches, malformed versions, older active release runs, and versions whose exact branch or tag already exists. The mutation phase is serialized and also rejects a changed `master` commit before writing anything.

The repository and organization policies must allow the workflow's declared token permissions to take effect: `actions: read` for overlap detection and `contents: write` for the version commit, branches, tags, and draft release. Rules protecting `master` must also permit this workflow's GitHub Actions identity to push the version commit. If policy blocks either capability, keep the protection in place and adjust the release process deliberately; do not broaden permissions without reviewing the repository rules.

The workflow creates a draft GitHub Release. Review and publish that draft separately; creating refs does not publish the release announcement automatically.

Recovery depends on the last completed mutation:

- If validation failed or no version commit was pushed, fix the cause, review current `master`, and dispatch again.
- If the version commit reached `master` but neither exact reference exists, dispatching the same version again can reuse that commit.
- If the exact branch or exact tag exists, do not rerun the workflow for that version. Inspect the remote state and manually complete any missing moving/exact refs and draft release. Never move an exact ref.
- If only draft-release creation failed, create the draft manually from the existing exact tag.
- If a published release is bad, repoint moving aliases where appropriate and issue a new patch. Exact refs remain evidence of what was published.

The early overlap check makes the newer run fail instead of silently waiting behind an older manual release. The serialized mutation job and stale-`master` check are still the authoritative race protection.

See [Release reference policy](decisions/2026-09-04-release-reference-policy.md) for the stability guarantees behind these rules.

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
