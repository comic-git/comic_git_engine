<!-- ai-agent-toolkit:managed version="1.0.0" -->

# CMS

| Field      | Value                        |
|------------|------------------------------|
| **Status** | `vertical slice implemented` |

## Summary

This feature covers the optional Decap CMS editing workflow for `comic_git`.

It includes the static admin surface, the TOML-backed content model, migration rules from legacy files, and the boundary between `comic_git_engine` and the future hosted GitHub App / OAuth backend.

## Current State

The first engine-side vertical slice is implemented and has completed a local
browser round trip against `comic_git_dev`. It generates a static `/admin/`
surface for editing TOML-backed comic pages in the main comic and Extra Comics.
The hosted GitHub OAuth backend is not implemented, so production sign-in is
still deferred.

Current behavior:

- CMS is optional and site-wide
- the engine remains a static-site build engine
- TOML is the editable source format for future CMS-managed content
- migrated TOML files become the source of truth for the logical items they replace
- enabling CMS generates marked `admin/index.html` and `admin/config.yml`
- the initial editor manages comic pages, not site/comic configuration
- all page folders must be safely editable before any admin files are written
- page deletion and the built-in content preview are disabled in the first slice
- `--cms-local-backend` switches only the current process to Decap's local
  proxy; it never becomes a deployable config setting
- TOML-backed repos still build normally when CMS output is disabled

The safety gate currently requires every main and Extra Comic page folder to
contain valid `info.toml` with a nonblank title and date-only `post_date`.
Nonempty `[transcripts]`, `[social_media]`, and `[extra]` tables must be
managed manually until the CMS can preserve them.

## Local Proof Workflow

From a CMS-enabled host repo, run the Decap proxy and the comic_git development
server in separate terminals:

```text
npx decap-server
python comic_git_engine/src/scripts/dev_server.py --cms-local-backend
```

Then open the built site's `/admin/` URL. The local-backend flag does not
bypass the readiness checks and does not alter `comic_info.toml`.

## Product Rules

- CMS must remain optional.
- Git remains the source of truth.
- The underlying repo structure should remain understandable to manual editors.
- CMS migration behavior must be deterministic and documented.
- Local proxy configuration must never leak into production output by accident.
- Generated admin cleanup must preserve user-owned files.
- Refactors in this area should be reviewed carefully because they affect both build behavior and future external tooling.

## Supporting Documents

| Document | Contents |
|----------|----------|
| [plan.md](plan.md) | The current Decap CMS implementation plan, scope, risks, and phased rollout direction |
| [comic-info-toml-format.md](comic-info-toml-format.md) | The provisional comic-level TOML schema and legacy config mapping |
| [page-toml-format.md](page-toml-format.md) | The current page-level TOML contract and legacy migration rules |
