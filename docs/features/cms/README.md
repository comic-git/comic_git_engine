<!-- ai-agent-toolkit:managed version="1.0.0" -->

# CMS

| Field      | Value     |
|------------|-----------|
| **Status** | `planned` |

## Summary

This feature covers the planned CMS-backed editing workflow for `comic_git`.

It includes the static admin surface, the TOML-backed content model, migration rules from legacy files, and the boundary between `comic_git_engine` and the future hosted GitHub App / OAuth backend.

## Current State & Roadmap

The CMS work is still in active design and PoC implementation.

Current direction:

- CMS is optional and site-wide
- the engine remains a static-site build engine
- TOML becomes the editable source format for CMS-managed content
- migrated TOML files become the source of truth for the logical items they replace
- the hosted GitHub App and OAuth backend remain out of scope for the engine repo, but the engine must integrate cleanly with them

Important current behavior:

- TOML loading is intended to be mode-agnostic once a repo is migrated
- page-level `info.toml` support is the first concrete TOML read path
- the migration flow is intended to be one-way
- admin output is planned but not implemented yet

## Product Rules

- CMS must remain optional.
- Git remains the source of truth.
- The underlying repo structure should remain understandable to manual editors.
- CMS migration behavior must be deterministic and documented.
- Refactors in this area should be reviewed carefully because they affect both build behavior and future external tooling.

## Supporting Documents

| Document | Contents |
|----------|----------|
| [plan.md](plan.md) | The current Decap CMS implementation plan, scope, risks, and phased rollout direction |
| [comic-info-toml-format.md](comic-info-toml-format.md) | The provisional comic-level TOML schema and legacy config mapping |
| [page-toml-format.md](page-toml-format.md) | The current page-level TOML contract and legacy migration rules |
