<!-- ai-agent-toolkit:managed version="1.0.0" -->

# Transcripts

| Field      | Value    |
|------------|----------|
| **Status** | `active` |

## Summary

This feature adds per-page transcript support to comic pages, including multiple transcript languages and configurable transcript source locations.

Transcripts are part of the page-publishing model rather than a separate site-wide content system, but they have their own loading and precedence rules.

## Current State & Roadmap

The current transcript model is intentionally flexible:

- transcripts can be loaded from each comic page folder
- transcripts can also be loaded from a separate transcripts directory
- both sources can be used at the same time
- a configured default language can be promoted ahead of the normal sort order

Important current behavior:

- transcripts are opt-in through the `[Transcripts]` section
- `post.txt` is intentionally excluded from transcript loading
- Markdown and HTML are both supported in transcript source files
- if both `.txt` and `.md` exist for the same language, the Markdown file takes precedence
- transcript files are tolerated in either UTF-8 or Latin-1 to support inconsistent real-world contributor input

This feature is stable in concept and closely tied to comic page rendering, but it remains sensitive to file-loading rules and fallback behavior.

## Product Rules

- Transcript support should remain easy to use from normal page folders without forcing users into a separate content-management system.
- Separate transcript folders should remain available for creators who need cleaner organization or contributor workflows.
- The feature should remain tolerant of inconsistent transcript file encodings when practical.
- Source precedence and default-language behavior should remain predictable and documented.
- Refactors in this area should be reviewed carefully because transcript loading rules affect visible page content and contributor workflows.

## Supporting Documents

| Document | Contents |
|----------|----------|
| [../comic-pages-and-publishing/](../comic-pages-and-publishing/) | The broader page-publishing model that transcript loading attaches to |
