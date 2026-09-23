<!-- ai-agent-toolkit:managed version="1.0.0" -->

# Page TOML Format

## Purpose

This document defines the current TOML migration contract for comic pages.

The engine read path and migration writer use these same rules instead of re-inventing the schema in two places.

## Scope

This contract is page-scoped only.

It defines how one legacy page folder becomes one `info.toml` file and how that TOML file maps into the engine's structured page and image source models.

The page ID is not stored in TOML. It is derived from the containing folder name.

It does not define the TOML schema for:

- `comic_info.toml`
- site-level social media defaults
- webring participation settings
- Extra Comic config inheritance

## CMS Compatibility

The first CMS editor exposes `title`, ordered `images`, `post_date`,
`post_text`, `alt_text`, `thumbnail`, `storyline`, `characters`, and
`tags`. New pages may be image-backed or text-only, and uploaded images stay
beside the page's `info.toml`.

For the complete boundary between valid engine input and the narrower set that
the CMS can safely save, see [mvp-toml-contract.md](mvp-toml-contract.md).

CMS enablement is deliberately all-or-nothing across the main comic and every
Extra Comic. Each page folder must have valid `info.toml`, a nonblank
`title`, and a quoted, date-only ISO `post_date`. Native TOML dates remain
valid engine input, but CMS-managed pages use strings so Decap does not turn a
calendar date into a timezone-sensitive browser timestamp. The CMS can edit
page `[transcripts]` and `[social_media]` tables when every key is nonblank and
every value is a string. Transcript values use Decap's Rich Text/Markdown editor. Timestamp post
dates and nonempty `[extra]` tables remain valid engine inputs, but must be
removed or managed manually before this CMS slice can be enabled because its
form cannot yet round-trip them safely.

New page folders are derived from the initial title. Duplicate titles are valid:
path-aware collision suffixing creates a sibling bundle such as
`same-title-1/info.toml`, while later title edits preserve the page folder.

By contrast, numbered metadata siblings such as `info-1.toml` and
`info_2.toml` are invalid. They indicate that an older or unpatched Decap build
put the collision suffix on the metadata filename inside the existing page
folder. The engine rejects them with recovery guidance instead of silently
ignoring the attempted page.

The CMS does not delete page entries, does not rename an existing page folder
when its title changes, and does not provide a content preview in this slice.
Because the folder name is the page's path-derived identity, manually renaming
it changes the page URL, page and image IDs, and generated image anchor IDs. The
engine does not create a redirect from the old URL.

## Page Schema

Current engine-owned schema:

```toml
post_date = "2024-01-02"
title = "Chapter One"
alt_text = """
Page-level hover description fallback
"""
screen_reader_text = "Page-level image description for screen readers"
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
alt_text = "Hover description"
screen_reader_text = "Alice enters the room."
thumbnail = "page-1-thumbnail.jpg"

[[images]]
filename = "page-2.png"

[extra]
"Mood" = "tense"
```

`images` is always an ordered array of tables. `filename` is required in each
table. `title`, `alt_text`, `screen_reader_text`, and `thumbnail` are optional:

- omitted `title` uses the configured image-title fallback
- omitted `alt_text` inherits the page `alt_text`; despite its historical name,
  this value supplies the HTML `title` hover description
- omitted `screen_reader_text` inherits the page `screen_reader_text`, then the
  resolved `alt_text` value for backward compatibility; it supplies HTML `alt`
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

1. `Post date` becomes a quoted `post_date` string in normalized ISO date or
   datetime format.
2. `Filename` or `Filenames` becomes ordered `[[images]]` tables.
3. Ordered `[Image <label>]` sections become ordered `[[images]]` tables,
   preserving per-image title, hover text, screen-reader text, and thumbnail
   presence.
4. If no explicit filename field or image section exists, migration writes the
   current auto-discovered image list as image tables.
5. `post.txt` becomes `post_text`.
6. Page-local transcript source files become the `[transcripts]` table.
7. A page-local `social_media.json` with a top-level `comic` object migrates that object into `[social_media]`.
8. Known legacy fields become first-class TOML fields.
9. Unknown legacy `info.ini` keys are preserved under `[extra]`.
10. `!private` keys are not migrated.
11. The page folder name remains path-derived identity and is not duplicated into `info.toml`.

When migration also enables CMS, a missing or blank legacy `Title` is written
as the resolved page title: the first image filename without its extension, or
the page folder name for an image-free page. Ordinary TOML migration leaves an
omitted title omitted, preserving the live title fallback behavior.

## Read-Path Rules

When `info.toml` exists for a page:

1. it is the source of truth for page metadata
2. inline TOML `post_text` replaces page-local `post.txt`
3. inline TOML `[transcripts]` replaces legacy transcript files for that page
4. inline TOML `[social_media]` replaces page-local `social_media.json`
5. site-level `before post text.*` and `after post text.*` files still apply because they are not page-local source files

`post_date` accepts quoted ISO dates and datetimes as well as TOML's native date
and datetime values. A datetime without an offset uses the comic's configured
timezone. A datetime with an offset represents that exact instant and is
converted to the comic's timezone for display and scheduling.

CMS-managed pages currently narrow that general engine contract to quoted
`YYYY-MM-DD` strings. Future time-of-day CMS work will explicitly compare native
TOML and quoted ISO datetime round trips before choosing its write format; the
current date-only restriction does not decide that future representation.

## Notes

- This schema intentionally preserves explicit image ordering.
- This schema intentionally avoids legacy image auto-discovery in TOML mode.
- The page folder plus image filename remains the source of image identity;
  the owning comic path is added during normalization to prevent Extra Comic
  collisions.
- The `[extra]` table exists to preserve compatibility with custom template fields and hook logic during migration.
- Migration preserves the `post_date` date and, when present, time, but not the exact legacy display spelling. The TOML read path formats the normalized ISO value with the configured site date format, so a legacy value such as `August 1, 2025` may render as `August 01, 2025` when the format uses `%d`.
