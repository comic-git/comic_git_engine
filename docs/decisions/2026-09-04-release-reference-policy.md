<!-- ai-agent-toolkit:managed version="1.0.0" -->

# Release reference policy

| Field             | Value      |
|-------------------|------------|
| **Date**          | 2026-09-04 |
| **Status**        | `active`   |
| **Supersedes**    |            |
| **Superseded by** |            |

## Context

comic_git consumers can independently select a reusable workflow revision and an engine revision. Both selectors need convenient patch updates by default, while maintainers and users also need immutable references for reproducible builds and recovery.

Moving a major reference automatically has an unusually large compatibility surface. In particular, the existing `v1` workflow tag represents the 1.0 workflow contract and must remain frozen. Major reference changes are rare enough that deliberate manual management is safer than encoding them in normal patch-release automation.

## Decision

Publish and manage release references according to their stability promise:

- `latest`, the minor branch such as `1.1`, and the minor workflow tag such as `v1.1` are moving references. A patch release advances them to the new release commit.
- An exact branch such as `1.1.0` and exact tag such as `v1.1.0` are immutable. Release automation must refuse to overwrite either one.
- Major tags are manual. The release workflow must not create, move, or delete them. The `v1` tag remains frozen at the 1.0 workflow contract.
- The workflow revision in `uses: comic-git/comic_git_engine/.github/workflows/build_site.yaml@...` and the engine version in host configuration remain independent selectors. The normal 1.1 defaults are `@v1.1` and engine version `1.1`; users can pin both to `v1.1.0` and `1.1.0` for exact reproducibility.

The release workflow accepts a complete canonical `X.Y.Z` version and runs only from `master`. Before mutation it rejects overlapping release runs and existing exact references, then records the reviewed `master` commit. The mutation job is serialized and refuses to continue if `master` changed after validation. Successful automation creates a draft GitHub Release so publication remains a deliberate maintainer action.

## Consequences

Patch releases can reach default 1.1 consumers without changing either selector, while exact pins remain stable. A future major workflow contract requires a separate, explicit decision and manual tag operation.

Failure recovery depends on how far the workflow progressed:

- Before the version commit: correct the problem, review current `master`, and dispatch a new run.
- After the version commit but before any exact reference exists: a new run for the same version can safely reuse the existing commit after preflight succeeds.
- After any exact reference exists: do not rerun the automated release for that version. Inspect all refs and finish missing references or the draft release manually without moving an exact ref.
- After publishing a defective release: advance moving references to a known-good release as needed and publish a new patch for the correction. Exact references remain unchanged.

The overlap check is an early guard, not the only race protection. Serialized mutation and the recorded-`master` check remain necessary because GitHub Actions can dispatch runs close together.

## Files Affected

- `.github/workflows/main.yaml`
- `.github/workflows/build_site.yaml`
- `docs/cicd.md`
- `docs/contributing.md`
- `docs/infrastructure.md`
