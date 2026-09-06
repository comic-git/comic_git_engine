<!-- ai-agent-toolkit:managed version="1.0.0" -->

# CMS uses an all-page safety gate and runtime-only local backend

| Field             | Value      |
|-------------------|------------|
| **Date**          | 2026-09-05 |
| **Status**        | `active`   |
| **Supersedes**    |            |
| **Superseded by** |            |

## Context

Decap CMS rewrites a complete entry when it saves. The first comic_git form
cannot represent every valid page shape, so allowing it to open only some
fields could silently discard transcripts, social-media overrides, custom
metadata, timestamps, or legacy-only content.

Local Decap testing also requires a proxy-specific backend configuration. If
that mode were stored in `comic_info.toml`, it could be committed and published
accidentally.

## Decision

CMS enablement is site-wide and all-or-nothing for page content. Before writing
admin output, inspect every page folder in the main comic and all Extra Comics
and report every incompatible page in one error. Expand the accepted set only
when the generated form can safely round-trip the newly supported data.

Select Decap's local proxy only through the `--cms-local-backend` runtime flag.
There is no persistent TOML key for local mode. Production output continues to
require explicit GitHub/OAuth backend information.

## Consequences

Creators cannot use the first CMS slice on a partially migrated or more complex
site until all pages meet the supported contract. That is intentionally stricter
than normal engine loading, but it prevents lossy saves and gives one actionable
list of required fixes.

Local testing needs two processes, but its backend mode cannot leak into a
deployment through a committed setting.

## Files Affected

- `src/build/output/cms.py`
- `src/build/build_site.py`
- `src/scripts/dev_server.py`
- `templates/cms/`
- `tests/build/output/test_cms.py`
- `tests/build/test_build_site.py`
- `tests/scripts/`
- `docs/features/cms/`
- `docs/gotchas.md`
- `docs/architecture.md`
