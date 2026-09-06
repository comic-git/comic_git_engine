<!-- ai-agent-toolkit:managed version="1.0.0" -->

# Comic pages and publishing

| Field      | Value    |
|------------|----------|
| **Status** | `active` |

## Summary

This feature covers the core workflow of turning user-managed comic page folders into published comic pages on the final site.

It includes page-level source files, page discovery rules, publishing-time inclusion and exclusion behavior, and the generated page metadata that other site features depend on.

## Current State & Roadmap

The current design favors low-friction publishing for non-technical users:

- a comic page is primarily a folder in `your_content/comics/`
- image files can be auto-discovered instead of always being declared explicitly
- page titles can fall back to image filenames
- a creator can often publish a page by creating a folder, adding an image, and setting a post date

Important current behavior:

- a page remains the scheduling, navigation, post-text, tag, and RSS publishing unit
- each page owns an ordered collection of zero or more structured comic images
- each image has a resolved archive title, hover description, screen-reader text,
  and thumbnail data; its ordered array position determines its presentation
  anchors
- future-dated pages are treated as scheduled posts and are not published by default
- local development may opt into previewing future posts
- generated page metadata is versioned and validated by a deployed JSON Schema
- public image metadata omits internal IDs and anchors; `filename`, `url`, and
  ordered array position are the public locator/order contract
- page-level source metadata can include private values that are stripped from public metadata output
- explicit `Filename` or `Filenames` values override image auto-discovery
- structured INI pages use ordered `[Image <label>]` sections; these cannot be
  mixed with page-level `Filename` or `Filenames`
- TOML pages use ordered `[[images]]` tables and do not auto-discover images
- image files whose names start with `_` are intentionally excluded from image auto-discovery
- standalone pages use `#comic-image-N`; infinite scroll derives
  `#<page-name>_<minimum-two-digit-N>` independently
- the archive defaults to one entry per page; image-bearing page entries link
  to `#comic-image-1`, while text-only page entries link to `#post-body`
- optional image mode emits one entry per image and links each entry to its
  standalone positional anchor
- image-mode archives include text-only posts by default; `Show text-only posts
  = False` / `archive.show_text_only_posts = false` hides them without changing
  page-mode archives
- configured `[Pages]` entries remain authoritative; character and tag metadata
  does not implicitly enable the `tagged` page or generate tag archives
- when `tagged` is configured, the built-in comic template links character and
  tag values to their archives; otherwise it displays the same ordered values as
  plain text and logs one actionable warning for the affected comic
- no-image pages keep their post, navigation, RSS item, and page archive entry
- generated sites are staged into `build/` by default; an empty output-directory
  setting retains the legacy in-place build mode

This feature is under active long-term architectural pressure from the roadmap:

- destructive scheduled-post deletion is legacy behavior that should eventually be replaced by selective publishing
- generated output structure may continue to evolve independently now that build
  output is staged separately from host-repo source by default

## Product Rules

- The minimum publishing workflow should stay simple and approachable for non-technical users.
- Sensible auto-discovery and fallback behavior is preferred when it reduces repetitive work without making behavior surprising.
- Explicit page-file declarations should remain available when users need to override automatic discovery.
- Scheduled publishing must protect creators from accidentally exposing future comic content.
- Generated metadata such as `page_info_list.json` is part of the product contract and should be treated as intentional output.
- Image fallback rules are resolved while normalizing source data. Templates,
  feeds, JavaScript, and hooks consume resolved values rather than independently
  repeating fallback logic.
- The historically named `Alt text` / `alt_text` source value supplies the HTML
  `title` hover description. `Screen reader text` / `screen_reader_text` supplies
  the HTML `alt` text alternative. When the newer field is omitted, it inherits
  the legacy value so existing pages retain their accessible description.
- Internal image identity is derived from owning comic, page folder, and
  normalized filename for thumbnail processing. It is not a public metadata or
  anchor contract.
- Missing optional site pages must not make otherwise valid page metadata
  disappear or create broken built-in links. The build should preserve the
  metadata, explain the disabled behavior, and continue successfully.
- Refactors in this area should be tested carefully because many other features depend on page ordering, page metadata, and page inclusion rules.

## Supporting Documents

| Document | Contents |
|----------|----------|
| [../../decisions/2026-04-12-low-friction-page-publishing.md](../../decisions/2026-04-12-low-friction-page-publishing.md) | Why page publishing favors image and title fallbacks with minimal required user input |
| [../../decisions/2026-04-12-public-output-filtering-and-metadata-exposure.md](../../decisions/2026-04-12-public-output-filtering-and-metadata-exposure.md) | Why generated metadata is published intentionally and how private page fields are filtered |
| [../../roadmap.md](../../roadmap.md) | Future migration direction for output-directory-first builds and non-destructive scheduled-post publishing |
