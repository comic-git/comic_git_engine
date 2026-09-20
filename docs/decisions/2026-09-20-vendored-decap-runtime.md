<!-- ai-agent-toolkit:managed version="1.0.0" -->

# Vendor the temporary Decap CMS runtime

| Field             | Value      |
|-------------------|------------|
| **Date**          | 2026-09-20 |
| **Status**        | `active`   |
| **Supersedes**    |            |
| **Superseded by** |            |

## Context

comic_git needs Decap's path-aware collision-suffix fix before its CMS can
create reliable nested page bundles. The focused upstream pull request may take
an unknown amount of time to merge and release. Loading a moving fork branch or
an unofficial CDN artifact would make a creator's deployed CMS depend on
external mutable state.

## Decision

Until an upstream Decap release contains the required behavior, commit the
reviewed fork's built browser runtime into `comic_git_engine`. Each runtime uses
a new versioned directory containing the entry script, lazy-loaded JavaScript
chunks, required WASM files, license notice, and a manifest. The manifest
records the upstream version, fork commit, build command, and SHA-256 of every
runtime asset.

CMS output copies that directory under `admin/vendor/` and uses a relative
script URL. This keeps site builds and deployed CMS pages independent of Node,
npm, CDNs, and a local Decap checkout. The engine only removes runtime
directories carrying its manifest marker, so `admin/` assets owned by a host
repo remain intact.

## Consequences

The engine commit is the immutable pin for the exact browser code that users
receive, and browser tests exercise the same runtime by default. This is a
focused private distribution mechanism, not a published replacement Decap
package.

Vendored assets increase repository and generated-site size, and Decap security
updates require a deliberate rebuild, manifest refresh, review, and test pass.
Do not overwrite an existing runtime directory or load a moving fork ref. When
an upstream release contains the required behavior, replace the vendored runtime
with that reviewed release through the same versioned process or deliberately
retire vendoring after validating the upstream distribution.

## Files Affected

- `vendor/decap-cms/`
- `src/build/output/cms.py`
- `src/build/output/site_output.py`
- `src/scripts/dev_server.py`
- `templates/cms/`
- `tests/build/output/test_cms.py`
- `tests/build/output/test_site_output.py`
- `tests/scripts/test_entrypoints.py`
- `docs/features/cms/`
- `../e2e_tests/e2e_harness/cms_browser.py`
- `../e2e_tests/tests/browser/`
- `../e2e_tests/tests/generated_site_contracts/test_cms.py`
