<!-- ai-agent-toolkit:managed version="1.0.0" -->

# Low-friction page publishing

| Field             | Value      |
|-------------------|------------|
| **Date**          | 2026-04-12 |
| **Status**        | `active`   |
| **Supersedes**    |            |
| **Superseded by** |            |

## Context

Uploading comic pages is repetitive work. Reducing the number of required steps is a direct quality-of-life improvement for creators.

Earlier versions required more explicit configuration, such as always specifying image filenames. That proved unnecessary and caused avoidable broken builds.

## Decision

Favor defaults and auto-discovery that reduce the minimum work required to publish a page.

- If `Filename` or `Filenames` is omitted, discover page images automatically from the page folder.
- Exclude files whose names start with `_` from automatic page-image discovery.
- Allow page titles to fall back to the first discovered image filename when no explicit `Title` is set.
- Keep explicit `Filename`/`Filenames` support so creators can override discovery when needed.

The intended minimum workflow for many pages is:

1. create a new page folder
2. add the image file
3. add an `info.ini` with a Post Date

## Consequences

This reduces user effort and makes common publishing flows faster.

It also means:

- image-folder conventions matter because they are part of the user experience
- `_`-prefixed files serve as an intentional escape hatch for non-page images and generated assets such as thumbnails
- refactors should preserve these fallbacks unless a replacement is clearly better for non-technical users

## Files Affected

- `scripts/build_site.py`
- `your_content/comics/*/info.ini`
- `docs/architecture.md`
- `docs/coding-principles.md`
