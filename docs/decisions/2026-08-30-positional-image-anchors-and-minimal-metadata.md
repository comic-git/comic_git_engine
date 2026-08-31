<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: AI agents and developers changing comic/image models, metadata, navigation, archives, or infinite scroll.
     Purpose: Preserve why image anchors are positional and public image metadata excludes internal identity. -->

# Positional image anchors and minimal public metadata

| Field             | Value      |
|-------------------|------------|
| **Date**          | 2026-08-30 |
| **Status**        | `active`   |
| **Supersedes**    |            |
| **Superseded by** |            |

## Context

Comic pages own an ordered array of zero or more images. Standalone pages,
archives, and infinite scroll need predictable links into that order, while
public metadata consumers need image content and location without depending on
engine implementation identity.

Anchors should therefore be readable and derivable from rendering context rather
than stored as image data. Pages may also contain no images, so page navigation
needs a meaningful destination that does not assume an image wrapper exists.

## Decision

The ordered `images` array is authoritative for presentation order. Standalone comic images use one-based `comic-image-N` fragments. Infinite-scroll images derive `<page-name>_<minimum-two-digit-N>` fragments at runtime; a bare page-name fragment remains an accepted input alias for that page's first image. Post-oriented archive entries use `post-body`, while tagged listings link to the page URL without a fragment so they represent the complete comic page.

Public image metadata contains only `filename`, `url`, resolved `title`, resolved `alt_text`, and `thumbnail_url`. It contains no image `id`, anchor, or index. `ComicImage.id` is an internal thumbnail-identity input and must not leak into public metadata. Archive image indices are internal projections, and infinite-scroll chapter controls use a separate image-bearing-page projection rather than archive entries.

## Consequences

- Image links are readable and deterministic from array order, but reordering images intentionally changes their fragments.
- Renaming an image without moving it preserves its positional fragment.
- Navigation targets `comic-image-1` for image-bearing pages and `post-body` for text-only pages.
- Themes and integrations derive image position from list order rather than an image ID or stored anchor.
- Schema version 1 defines the minimal public image shape without an ID, anchor, or index.
- The internal image ID remains coupled to generated-thumbnail naming; changing that identity requires a separate thumbnail-cache design.

## Files Affected

- `src/build/content/page_models.py`
- `src/build/content/page_discovery.py`
- `src/build/content/comic_data.py`
- `src/build/content/page_metadata.py`
- `src/build/site_builder.py`
- `schemas/page_info_list.schema.json`
- `templates/comic.tpl`
- `templates/navigation_bar.tpl`
- `templates/archive.tpl`
- `templates/tagged.tpl`
- `templates/infinite_scroll.tpl`
- `js/infinite_scroll.js`
- `css/comic.css`
- `docs/features/comic-pages-and-publishing/README.md`
- `docs/features/code-hooks/README.md`
- `docs/features/themes-and-presentation-overrides/README.md`
