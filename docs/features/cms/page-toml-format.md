<!-- ai-agent-toolkit:managed version="1.0.0" -->

# Page TOML Format

## Purpose

This document defines the current TOML migration contract for comic pages.

The engine read path and migration writer use these same rules instead of re-inventing the schema in two places.

## Scope

This contract is page-scoped only.

It defines how one legacy page folder becomes one `info.toml` file and how that TOML file maps into the engine's structured page and image source models.

The page ID is not stored in TOML. It is derived from the containing folder name.

It does not yet define the final TOML schema for:

- `comic_info.toml`
- site-level social media defaults
- webring participation settings
- Extra Comic config inheritance

## Page Schema

Current engine-owned schema:

```toml
post_date = "2024-01-02"
title = "Chapter One"
alt_text = """
Page-level alt text fallback
"""
thumbnail = "_thumbnail.jpg"
storyline = "Arc 1"
characters = ["Alice", "Bob"]
tags = ["mystery", "noir"]

post_text = """
Page-local post text from post.txt
"""

[transcripts]
English = """
Transcript text
"""

[social_media]
"og:title" = "Custom override"

[[images]]
filename = "page-1.png"
title = "Opening panel"
alt_text = "Alice enters the room."
thumbnail = "page-1-thumbnail.jpg"

[[images]]
filename = "page-2.png"

[extra]
"Mood" = "tense"
```

`images` is always an ordered array of tables. `filename` is required in each
table. `title`, `alt_text`, and `thumbnail` are optional:

- omitted `title` uses the configured image-title fallback
- omitted `alt_text` inherits the page `alt_text`
- omitted `thumbnail` uses the resolved thumbnail policy
- an explicitly blank value is preserved as an override instead of inheriting

This shape is provisional only where future CMS form behavior requires further
constraints. The engine contract is already structured and does not accept
string entries in `images`.

## Migration Rules

Legacy page folder inputs currently considered part of the page migration contract:

- `info.ini`
- page-local `post.txt`
- page-local transcript files
- page-local `social_media.json`
- explicit or auto-discovered page image filenames

Current conversion rules:

1. `Post date` becomes `post_date` in ISO `YYYY-MM-DD` format.
2. `Filename` or `Filenames` becomes ordered `[[images]]` tables.
3. Ordered `[Image <label>]` sections become ordered `[[images]]` tables,
   preserving per-image title, alt-text, and thumbnail presence.
4. If no explicit filename field or image section exists, migration writes the
   current auto-discovered image list as image tables.
5. `post.txt` becomes `post_text`.
6. Page-local transcript source files become the `[transcripts]` table.
7. A page-local `social_media.json` with a top-level `comic` object migrates that object into `[social_media]`.
8. Known legacy fields become first-class TOML fields.
9. Unknown legacy `info.ini` keys are preserved under `[extra]`.
10. `!private` keys are not migrated.
11. The page folder name remains path-derived identity and is not duplicated into `info.toml`.

## Read-Path Rules

When `info.toml` exists for a page:

1. it is the source of truth for page metadata
2. inline TOML `post_text` replaces page-local `post.txt`
3. inline TOML `[transcripts]` replaces legacy transcript files for that page
4. inline TOML `[social_media]` replaces page-local `social_media.json`
5. site-level `before post text.*` and `after post text.*` files still apply because they are not page-local source files

## Notes

- This schema intentionally preserves explicit image ordering.
- This schema intentionally avoids legacy image auto-discovery in TOML mode.
- The page folder plus image filename remains the source of image identity;
  the owning comic path is added during normalization to prevent Extra Comic
  collisions.
- The `[extra]` table exists to preserve compatibility with custom template fields and hook logic during migration.
- Migration preserves the `post_date` value, not the exact legacy display spelling. The TOML read path formats the ISO date with the configured site date format, so a legacy value such as `August 1, 2025` may render as `August 01, 2025` when the format uses `%d`.
