<!-- ai-agent-toolkit:managed version="1.0.0" -->

# Page TOML Format

## Purpose

This document defines the first concrete TOML migration contract for comic pages.

It exists so the engine read path and the future migration writer use the same rules instead of re-inventing the schema in two places.

## Scope

This contract is page-scoped only.

It defines how one legacy page folder becomes one `info.toml` file and how that TOML file maps back into the engine's existing internal page-info shape.

The page ID is not stored in TOML. It is derived from the containing folder name.

It does not yet define the final TOML schema for:

- `comic_info.toml`
- site-level social media defaults
- webring config
- Extra Comic config inheritance

## Page Schema

Current engine-owned schema:

```toml
post_date = "2024-01-02"
images = ["page.png"]
title = "Chapter One"
alt_text = """
Optional alt text
"""
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

[extra]
"Mood" = "tense"
```

## Migration Rules

Legacy page folder inputs currently considered part of the page migration contract:

- `info.ini`
- page-local `post.txt`
- page-local transcript files
- page-local `social_media.json`
- explicit or auto-discovered page image filenames

Current conversion rules:

1. `Post date` becomes `post_date` in ISO `YYYY-MM-DD` format.
2. `Filename` or `Filenames` becomes explicit `images`.
3. If no explicit filename field exists, the migration writes the current auto-discovered image list into `images`.
4. `post.txt` becomes `post_text`.
5. Page-local transcript source files become the `[transcripts]` table.
6. A page-local `social_media.json` with a top-level `comic` object migrates that object into `[social_media]`.
7. Known legacy fields become first-class TOML fields.
8. Unknown legacy `info.ini` keys are preserved under `[extra]`.
9. `!private` keys are not migrated.
10. The page folder name remains the page ID and is not duplicated into `info.toml`.

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
- The page folder name remains the single source of truth for page identity.
- The `[extra]` table exists to preserve compatibility with custom template fields and hook logic during migration.
