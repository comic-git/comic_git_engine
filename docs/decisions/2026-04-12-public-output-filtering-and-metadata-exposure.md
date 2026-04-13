<!-- ai-agent-toolkit:managed version="1.0.0" -->

# Public output filtering and metadata exposure

| Field             | Value      |
|-------------------|------------|
| **Date**          | 2026-04-12 |
| **Status**        | `active`   |
| **Supersedes**    |            |
| **Superseded by** |            |

## Context

Built output is not only for rendered HTML pages. It is also consumed by client-side JavaScript, feed readers, and external scrapers.

At the same time, not every piece of source metadata should become public just because it exists in a page `info.ini`.

## Decision

Treat generated metadata as part of the public output contract, but allow lightweight source-level control over what is exposed.

- Generate `page_info_list.json` as published site output because client-side features and external tools need to fetch it.
- Strip page-info keys that start with `!` before writing public metadata output.
- Keep the filtering convention lightweight and file-based so creators can store internal-only page notes or metadata without inventing a separate system.

## Consequences

This supports rich static-site behavior while giving creators a simple way to avoid publishing some metadata.

It also means:

- `page_info_list.json` should be treated as a stable, intentional artifact rather than an incidental byproduct
- changes to page-info field exposure can affect both browser features and third-party consumers
- future refactors should preserve the `!` convention unless a better privacy-control mechanism replaces it explicitly

## Files Affected

- `scripts/build_site.py`
- `comic/page_info_list.json`
- `docs/architecture.md`
- `docs/integration/`
