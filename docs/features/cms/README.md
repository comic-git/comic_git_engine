<!-- ai-agent-toolkit:managed version="1.0.0" -->

# CMS

| Field      | Value     |
|------------|-----------|
| **Status** | `planned` |

## Summary

This feature covers the planned CMS-backed editing workflow for `comic_git`.

It includes the static admin surface, the TOML-backed content model, migration rules from legacy files, and the boundary between `comic_git_engine` and the future hosted GitHub App / OAuth backend.

## Current State & Roadmap

The TOML content foundation is implemented, while the browser-based CMS remains
in active design and PoC work.

Current direction:

- CMS is optional and site-wide
- the engine remains a static-site build engine
- TOML is the editable source format for future CMS-managed content
- migrated TOML files become the source of truth for the logical items they replace
- the hosted GitHub App and OAuth backend remain out of scope for the engine repo, but the engine must integrate cleanly with them

Important current behavior:

- the engine reads both comic-level `comic_info.toml` and page-level `info.toml`
- a TOML file takes precedence over the corresponding legacy INI file without merging same-item values
- the migration command deterministically converts supported legacy comic and page content, with legacy-file deletion kept as an explicit step
- TOML-backed repos build normally without enabling a CMS
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
