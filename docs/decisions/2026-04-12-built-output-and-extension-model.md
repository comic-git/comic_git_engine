<!-- ai-agent-toolkit:managed version="1.0.0" -->

# Built output and extension model

| Field             | Value      |
|-------------------|------------|
| **Date**          | 2026-04-12 |
| **Status**        | `active`   |
| **Supersedes**    |            |
| **Superseded by** |            |

## Context

comic_git targets static hosting first, especially GitHub Pages. It still needs modern webcomic features such as infinite scroll, RSS feeds, Extra Comics, and user-owned theme customization.

The engine also needs to balance central updatability with user control:

- built output must be directly consumable by browsers, client-side JS, and external tools
- default templates/styles/scripts should be fixable centrally
- user customizations must survive engine updates

## Decision

Use a static-output model with engine-owned defaults and host-owned extension points.

- Generate publishable artifacts directly into static site output, including machine-readable files such as `page_info_list.json`.
- Keep default templates, CSS, and JS in `comic_git_engine` so unmodified sites inherit fixes automatically.
- Allow user customization through host-repo theme/template/hook files rather than editing engine files directly.
- Load engine CSS first and user theme CSS after it, so CSS customization can be incremental.
- Support client-side features such as infinite scroll by generating static JSON data that browser JS can fetch at runtime.
- Treat per-comic behavior as belonging to the comic that owns the content when that produces clearer user-facing behavior, as with RSS title formatting.

## Consequences

This preserves a static-site deployment model while still supporting richer features and customization.

It also means:

- generated JSON and RSS output are part of the product contract, not incidental build artifacts
- template/CSS/JS changes in the engine can affect many users and need careful review
- theme hooks and overrides need to stay clearly separated from engine-owned files
- some functionality depends on client-side JavaScript even though the site is statically built

## Files Affected

- `scripts/build_site.py`
- `scripts/rss.py`
- `templates/`
- `default_files/css/`
- `default_files/js/`
- `themes/`
- `comic/`
- `page_info_list.json`
- `docs/architecture.md`
- `docs/integration/`
