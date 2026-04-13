<!-- ai-agent-toolkit:managed version="1.0.0" -->

# Compatibility and release policy

| Field             | Value      |
|-------------------|------------|
| **Date**          | 2026-04-12 |
| **Status**        | `active`   |
| **Supersedes**    |            |
| **Superseded by** |            |

## Context

Host `comic_git` repos automatically receive patch-level engine updates during normal builds. Most user data is stored in files, so a breaking engine change usually forces manual file edits by the user before their site builds again.

That makes accidental breakage unusually costly, especially for non-technical users. At the same time, releases still need confidence in generated output, docs sync, and workflow behavior.

## Decision

Treat compatibility and release discipline as product requirements.

- Patch releases must remain backward-compatible.
- Changes that would require users to edit existing files or workflows are not acceptable for patch releases.
- Major or minor breaking changes should be rare, batched where possible, and accompanied by migration guidance.
- Add or improve automated tests before refactors where practical, so existing behavior is locked down first.
- Manual release testing remains required, preferably through `comic_git_dev`.
- End-user docs in `comic_git_docs` should usually be updated near release time so published docs do not get ahead of released engine behavior.

## Consequences

This reduces the risk of surprising users with builds that suddenly break after an automatic patch update.

It also means:

- seemingly small behavior changes need compatibility review
- refactors need tests early, not only after code moves
- release work includes more than code merge: manual verification and docs sync are part of the release surface
- rollback and version-branch management matter because releases are user-facing infrastructure, not just tags

## Files Affected

- `scripts/**/*.py`
- `tests/`
- `.github/workflows/main.yaml`
- `.github/workflows/build_site.yaml`
- `docs/testing.md`
- `docs/contributing.md`
- `docs/coding-principles.md`
- `docs/cicd.md`
