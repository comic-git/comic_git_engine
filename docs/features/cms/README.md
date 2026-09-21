<!-- ai-agent-toolkit:managed version="1.0.0" -->

# CMS

| Field      | Value                        |
|------------|------------------------------|
| **Status** | `vertical slice implemented` |

## Summary

This feature covers the optional Decap CMS editing workflow for `comic_git`.

It includes the static admin surface, the TOML-backed content model, migration rules from legacy files, and the boundary between `comic_git_engine` and the future hosted GitHub App / OAuth backend.

## Current State

The engine-side editing slice is implemented. It generates a static `/admin/`
surface for editing the main comic settings and TOML-backed comic pages in the
main comic and Extra Comics. Page and settings editing have completed local
browser round trips against `comic_git_dev`. The hosted GitHub OAuth backend is
not implemented, so production sign-in is still deferred.

Current behavior:

- CMS is optional and site-wide
- the engine remains a static-site build engine
- TOML is the editable source format for future CMS-managed content
- migrated TOML files become the source of truth for the logical items they replace
- enabling CMS generates marked `admin/index.html` and `admin/config.yml`
- one creator-oriented Comic Settings page edits `your_content/comic_info.toml`
- common Comic Details, Website, Links, and Custom Pages settings appear first;
  less-common settings are grouped into collapsed sections
- page lists show each post date beside its title and default to newest first
- new page folders are derived from the initial title and remain stable when the
  title changes later; duplicate titles do not require a different temporary
  title
- Characters and Tags use compact comma-separated inputs that save TOML string arrays
- image items open expanded by default, with compact single-line inputs for
  their Hover text and Screen reader text
- collapsed image items use their explicit Title as a best-effort label and
  otherwise display Image
- the main config and all page folders must be safely editable before any admin
  files are written
- page deletion and the built-in content preview are disabled in the first slice
- `--cms-local-backend` switches only the current process to Decap's local
  proxy; it never becomes a deployable config setting
- TOML-backed repos still build normally when CMS output is disabled

The safety gate rejects invalid main config and nonempty `[legacy]` config
sections because the settings form cannot preserve arbitrary legacy values. It
also requires every main and Extra Comic page folder to contain valid
`info.toml` with a nonblank title and date-only `post_date`.
The date must be a quoted ISO string; native TOML dates remain valid for normal
engine builds but are rejected by CMS readiness to prevent browser-timezone
conversion and mixed-type sorting. Nonempty `[transcripts]`, `[social_media]`,
and `[extra]` tables must be managed manually until the CMS can preserve them.

The page collection uses `path: "{{slug}}/info"`. With Decap's path-aware
collision handling, duplicate title slugs create sibling bundles such as
`same-title-1/info.toml` instead of malformed metadata such as
`same-title/info-1.toml`. This has been validated against the local Decap fix,
and production output temporarily vendors that reviewed fork runtime. The
vendored runtime is replaced by an upstream Decap release when it contains the
required behavior.

## Vendored Decap Runtime

Until an upstream Decap release contains the path-aware collision fix, the
engine ships the exact browser runtime built from the reviewed
`comic-git/decap-cms` commit recorded in its manifest. CMS builds copy that
runtime under `admin/vendor/` and load it locally, so site builds and deployed
CMS pages do not depend on npm, a CDN, or a running Decap checkout.

The manifest records the source revision, build command, and SHA-256 of every
runtime asset. It retains JavaScript chunks, WASM files, and the license notice;
source maps and unused duplicate entry artifacts are intentionally omitted.
Each replacement gets a new versioned directory so browser caches cannot reuse
old contents. Tests verify the manifest, copied output, and safe cleanup of
engine-owned runtime directories while preserving user assets under `admin/`.
See [updating-vendored-decap-runtime.md](updating-vendored-decap-runtime.md)
for the maintainer procedure to build, verify, and replace that runtime.

## Future Date and Time Editing

Time-of-day publishing remains a separate CMS feature. Before enabling it, test
Decap's parsing, display, sorting, and save behavior for TOML native local dates,
local datetimes, and offset datetimes as well as quoted ISO values. Choose the
CMS representation only after that round-trip evidence is available; do not
assume that today's quoted date-only boundary determines the timestamp format.

The engine must continue accepting both native TOML date/datetime values and
quoted ISO date/datetime strings in the meantime. That broader read contract
lets the future CMS work improve native TOML support without migrating existing
non-CMS content or changing scheduling semantics first.

## Local Proof Workflow

From a CMS-enabled host repo, run the comic_git development server:

```text
python comic_git_engine/src/scripts/dev_server.py --cms-local-backend
```

Then open the built site's `/admin/` URL. The local-backend flag does not
bypass the readiness checks and does not alter `comic_info.toml`. The development
server starts `npx decap-server` and stops it when the development server exits.

To load a bundle from a built local Decap checkout, replace the second command
with:

```text
python comic_git_engine/src/scripts/dev_server.py --decap-cms-repo ../decap-cms
```

This implies `--cms-local-backend` and reinstalls the local bundle after each
site rebuild. Fork-specific configuration remains an explicit engine-template
change so selecting a checkout cannot silently alter collection behavior.

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
| [mvp-toml-contract.md](mvp-toml-contract.md) | The implemented CMS-safe TOML subset, readiness gate, deployment preconditions, and deferred source shapes |
| [comic-info-toml-format.md](comic-info-toml-format.md) | The provisional comic-level TOML schema and legacy config mapping |
| [page-toml-format.md](page-toml-format.md) | The current page-level TOML contract and legacy migration rules |
| [updating-vendored-decap-runtime.md](updating-vendored-decap-runtime.md) | Maintainer procedure for replacing the versioned Decap runtime |
