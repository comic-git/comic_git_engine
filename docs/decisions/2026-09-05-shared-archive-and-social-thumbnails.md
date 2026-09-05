<!-- ai-agent-toolkit:managed version="1.0.0" -->

# Shared archive and social thumbnails

| Field             | Value      |
|-------------------|------------|
| **Date**          | 2026-09-05 |
| **Status**        | `active`   |
| **Supersedes**    |            |
| **Superseded by** |            |

## Context

Generated page and image thumbnails are used in the Archive and exposed to
social-media previews and public page metadata. Separate files optimized for
each consumer could improve social-preview resolution, but would add build work,
storage, filenames, configuration, and ownership rules for non-technical users.

The default Archive layout uses 100-pixel-wide cards and constrains thumbnail
images to the card width. A percentage-based generation default only produces a
100-pixel-wide file when the source happens to be 1000 pixels wide; other source
sizes produce inconsistent results or files larger than the Archive displays.

## Decision

Use the same generated thumbnail files for Archive entries, social-media
previews, and public metadata. Do not create separate consumer-specific
thumbnail variants by default.

When `Thumbnail size` is omitted, generate thumbnails at `100w`: 100 pixels wide
with proportional height. Users who want higher-resolution shared thumbnails can
set a larger width. The default Archive CSS continues to display those files at
no more than 100 pixels wide.

## Consequences

Thumbnail generation remains fast, storage stays small, and creators have one
file convention and one size setting to understand. Generated thumbnails match
the default Archive layout predictably regardless of source-image dimensions.

The default 100-pixel files may be lower resolution than ideal for some social
platforms or high-density displays. A creator can choose a larger generated size
or provide an explicit thumbnail; the Archive will resize it in the browser.
Future changes should not introduce separate Archive and social thumbnail files
without revisiting this simplicity and storage tradeoff.

## Files Affected

- `src/build/output/images.py`
- `src/core/utils.py`
- `src/build/content/page_metadata.py`
- `templates/archive.tpl`
- `css/archive.css`
- `tests/build/output/test_images.py`
- `../comic_git_docs/basic-editing/editing-your-comic-info.md`
