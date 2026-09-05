<!-- ai-agent-toolkit:managed version="1.0.0" -->

# Comic Info TOML Format

## Status

Implemented as the current `comic_info.toml` reader and migration contract. It remains provisional for CMS UX and may be revised if Decap editing exposes avoidable complexity.

## Purpose

This document defines the current TOML replacement for legacy comic-level config.

It covers:

- `your_content/comic_info.ini` -> `your_content/comic_info.toml`
- `your_content/<extra-comic>/comic_info.ini` -> `your_content/<extra-comic>/comic_info.toml`
- likely homes for site-level social media defaults and webring participation settings

It does not define page content. Page content is covered by [page-toml-format.md](page-toml-format.md).
It does not replace the public/shared `webring.json` endpoint data file.

## Format Principles

- Use snake_case keys to match page TOML.
- Keep the file readable for manual editors.
- Keep common creator-facing options near the top.
- Prefer explicit lists and arrays of tables over comma-delimited strings.
- Preserve the existing engine behavior unless a schema change is deliberate.
- Keep CMS settings site-wide and main-config-owned.
- Define every engine-supported option, but do not require every option to be present in every `comic_info.toml` file.
- Continue using code-owned defaults for omitted optional values.

When `comic_info.toml` exists for a logical comic config, it is the source of truth for that config. The loader does not merge same-item values from `comic_info.ini`.

The schema below is a supported-key contract, not a required full-file template. Migration and generated examples should stay sparse when code defaults are sufficient, so the TOML file remains approachable for manual editors.

The current reader accepts the engine-owned tables documented below through `[webring]`, plus `[[links]]`, `[[pages]]`, and `[legacy]`. Unknown top-level keys, unknown keys in engine-owned tables, and unsupported fields in link or page entries are rejected with the exact TOML path. This prevents misspelled settings from being silently ignored.

`[cms]` and `[social_media]` remain proposed schema areas for later CMS work. They are not accepted by the current reader until their engine behavior is implemented.

Extra Comics still inherit from the main comic config, but their own config file is an override file:

- extra `comic_info.toml` exists -> use it as the Extra Comic override source
- extra `comic_info.toml` absent -> fall back to extra `comic_info.ini`
- main config inheritance remains part of Extra Comic behavior

## Proposed Main Schema

```toml
[engine]
version = "1.1"

[comic]
name = "My Comic"
author = "Comic Creator"
description = "A webcomic about..."

[site]
theme = "default"
banner_image = "/your_content/images/banner.png"
date_format = "%B %d, %Y"
timezone = "America/Los_Angeles"
comic_domain = ""
comic_subdirectory = ""
extra_comics = ["extras/story"]
on_comic_click = "Next comic"
markdown_extras = []

[archive]
date_format = "%B %d, %Y"
use_thumbnails = true
show_uncategorized_comics = true
show_text_only_posts = true
list_images_separately = false
image_title_fallback = "page_title"

[navigation]
use_images = false
above_comic = false
below_comic = true
below_blurb = false

[transcripts]
enabled = false
load_from_comic_folder = true
folder = ""
default_language = "English"

[image_processing]
create_thumbnails = true
overwrite_existing_images = false
thumbnail_size = "200x200"

[analytics]
google_analytics_id = ""

[rss]
build = false
newest_first = false
language = "en-us"
image = ""
image_width = "144"
image_height = "144"
title_format = ""
channel_description = ""
combine_with_main = false

[cms]
enabled = false
editorial_workflow = false
backend_base_url = ""

[[links]]
name = "About"
url = "/about/"
open_in_new_tab = false

[[links]]
image_url = "example.com/button.png"
url = "https://example.com/"
open_in_new_tab = true

[[pages]]
template_name = "about"
title = "About"
```

## Proposed Social Media Defaults

Site-level social media defaults should probably move into `comic_info.toml`, but this is one of the areas most likely to change after CMS testing.

Proposed shape:

```toml
[social_media.base]
"og:type" = "website"
"og:title" = "{comic_title}"
"og:description" = "{comic_description}"

[social_media.comic]
"_inherits" = "base"
"og:type" = "article"
"og:title" = "{_title}"
```

The table names under `social_media` map to the existing template/data names used by social media preview generation. Arbitrary Open Graph or platform-specific keys remain string keys because they are external metadata names, not engine-owned option names.

## Proposed Webring Participation Config

The existing webring config currently has two concepts:

- engine settings in `comic_info.ini`
- endpoint/member data in `webring.json` or an external JSON URL

The first TOML pass should move only this site's participation settings into `comic_info.toml`:

```toml
[webring]
enabled = false
endpoint = ""
id = ""
show_all_members = false
exclude_own_comic_from_members = false
```

`webring.json` should remain a separate JSON endpoint/source-of-truth file. A single comic_git repo may publish `your_content/webring.json` as the canonical member list for a whole webring, and external callers may consume that JSON directly. CMS work may add editing support for that file later, but it should not be embedded into `comic_info.toml`.

## Legacy Mapping

| Legacy section       | Legacy option                          | TOML location                                |
|----------------------|----------------------------------------|----------------------------------------------|
| `Comic Settings`     | `Engine version`                       | `engine.version`                             |
| `Comic Info`         | `Comic name`                           | `comic.name`                                 |
| `Comic Info`         | `Author`                               | `comic.author`                               |
| `Comic Info`         | `Description`                          | `comic.description`                          |
| `Comic Settings`     | `Theme`                                | `site.theme`                                 |
| `Comic Settings`     | `Banner image`                         | `site.banner_image`                          |
| `Comic Settings`     | `Date format`                          | `site.date_format`                           |
| `Comic Settings`     | `Timezone`                             | `site.timezone`                              |
| `Comic Settings`     | `Comic domain`                         | `site.comic_domain`                          |
| `Comic Settings`     | `Comic subdirectory`                   | `site.comic_subdirectory`                    |
| `Comic Settings`     | `Extra comics`                         | `site.extra_comics`                          |
| `Comic Settings`     | `On comic click`                       | `site.on_comic_click`                        |
| `Comic Settings`     | `Markdown extras`                      | `site.markdown_extras`                       |
| `Archive`            | `Date format`                          | `archive.date_format`                        |
| `Archive`            | `Use thumbnails`                       | `archive.use_thumbnails`                     |
| `Archive`            | `Show Uncategorized comics`            | `archive.show_uncategorized_comics`          |
| `Archive`            | `Show text-only posts`                  | `archive.show_text_only_posts`               |
| `Archive`            | `List images separately`                | `archive.list_images_separately`             |
| `Archive`            | `Image title fallback`                  | `archive.image_title_fallback`               |
| `Navigation Bar`     | `Use images`                           | `navigation.use_images`                      |
| `Navigation Bar`     | `Above comic`                          | `navigation.above_comic`                     |
| `Navigation Bar`     | `Below comic`                          | `navigation.below_comic`                     |
| `Navigation Bar`     | `Below blurb`                          | `navigation.below_blurb`                     |
| `Transcripts`        | `Enable transcripts`                   | `transcripts.enabled`                        |
| `Transcripts`        | `Load transcripts from comic folder`   | `transcripts.load_from_comic_folder`         |
| `Transcripts`        | `Transcripts folder`                   | `transcripts.folder`                         |
| `Transcripts`        | `Default language`                     | `transcripts.default_language`               |
| `Image Reprocessing` | `Create thumbnails`                    | `image_processing.create_thumbnails`         |
| `Image Reprocessing` | `Overwrite existing images`            | `image_processing.overwrite_existing_images` |
| `Image Reprocessing` | `Thumbnail size`                       | `image_processing.thumbnail_size`            |
| `Google Analytics`   | `Tracking ID`                          | `analytics.google_analytics_id`              |
| `RSS Feed`           | `Build RSS feed`                       | `rss.build`                                  |
| `RSS Feed`           | `Newest first`                         | `rss.newest_first`                           |
| `RSS Feed`           | `Language`                             | `rss.language`                               |
| `RSS Feed`           | `Image`                                | `rss.image`                                  |
| `RSS Feed`           | `Image width`                          | `rss.image_width`                            |
| `RSS Feed`           | `Image height`                         | `rss.image_height`                           |
| `RSS Feed`           | `RSS title format`                     | `rss.title_format`                           |
| `RSS Feed`           | `Description`                          | `rss.channel_description`                    |
| `RSS Feed`           | `Combine with Main RSS Feed`           | `rss.combine_with_main`                      |
| `Webring`            | `Enable webring`                       | `webring.enabled`                            |
| `Webring`            | `Endpoint`                             | `webring.endpoint`                           |
| `Webring`            | `Webring ID`                           | `webring.id`                                 |
| `Webring`            | `Show all members`                     | `webring.show_all_members`                   |
| `Webring`            | `Exclude own comic from members`       | `webring.exclude_own_comic_from_members`     |
| `Links Bar`          | arbitrary option/value pairs           | `[[links]]`                                  |
| `Pages`              | arbitrary template/title pairs         | `[[pages]]`                                  |

## Notes

- `links` uses `name` for text links and `image_url` for image links. This avoids overloading the legacy option name.
- `pages` uses an array of tables so page order remains explicit.
- `engine.version` is read by the reusable build workflow before `comic_git_engine` is available in the host repo, so workflow parsing must support both `comic_info.ini` and `comic_info.toml`.
- Empty strings and default-looking values in the example represent supported keys and legacy-compatible values, not required file contents.
- Optional values may be omitted when the engine can provide the same behavior from code defaults.
- `archive.list_images_separately` defaults to `false`. Set it to `true` to create one archive entry per image instead of one entry per publishing page.
- `archive.show_text_only_posts` defaults to `true` and applies only when
  `archive.list_images_separately = true`. Page-based archives always include text-only posts.
- `archive.image_title_fallback` accepts `page_title` or `filename`.
- `image_processing.overwrite_existing_images` regenerates conventional page
  and identity-derived image thumbnails. Explicitly configured thumbnail files
  remain user-owned and are never overwritten.
- Migration may preserve unmapped legacy config values under a `[legacy]` table of section tables. That is a compatibility escape hatch for existing custom data, not the preferred home for new CMS-owned settings.
- A `[legacy]` entry may not duplicate a value supplied through a first-class TOML field, link, or page. Collisions are rejected so legacy compatibility data cannot silently overwrite first-class config.
- The final CMS UI may hide many of these fields even if the TOML schema supports them.
