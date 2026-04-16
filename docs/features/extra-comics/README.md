<!-- ai-agent-toolkit:managed version="1.0.0" -->

# Extra Comics

| Field      | Value    |
|------------|----------|
| **Status** | `active` |

## Summary

This feature allows one comic_git site to host multiple comics under separate subdirectories while keeping them within the same host repo and build.

Extra Comics behave like independent comics in many ways, but they inherit from the main comic by default and intentionally do not start with the same full page set as the main comic.

## Current State & Roadmap

The current Extra Comics model is built around inheritance plus selective override:

- an Extra Comic lives under its own folder in `your_content/`
- it inherits the main comic's settings by default
- it can override those settings with its own `comic_info.ini`
- it can use its own theme, links bar, pages, and RSS behavior

Important current behavior:

- by default, an Extra Comic provides comic pages only
- extra pages such as a homepage or archive are added only if the Extra Comic defines them
- the main comic's `[Pages]` section is not inherited automatically
- the main comic's `[Links Bar]` section is inherited unless the Extra Comic defines its own `[Links Bar]`
- Extra Comics can participate in RSS independently from the main comic, including overriding inherited RSS settings
- if an Extra Comic is configured to combine with the main RSS feed, it appears in the main feed instead of getting its own separate feed file

This feature is stable in concept and is a supported way to host related but distinct streams of content on one site.

## Product Rules

- Extra Comics should feel like real comics hosted on the same site, not just tagged subsets of the main comic.
- The default setup for an Extra Comic should stay lightweight: comic pages first, additional pages only when explicitly added.
- Inheritance should reduce setup work, while per-comic override points should remain available where users reasonably expect them.
- Refactors in this area should be reviewed carefully because Extra Comics cross several feature boundaries: page publishing, themes, links, and RSS.

## Supporting Documents

| Document | Contents |
|----------|----------|
| [../../decisions/2026-04-12-engine-and-host-repo-boundary.md](../../decisions/2026-04-12-engine-and-host-repo-boundary.md) | Why user-owned multi-comic content stays in the host repo while the engine handles the shared build logic |
| [../comic-pages-and-publishing/](../comic-pages-and-publishing/) | Core page-folder publishing behavior that Extra Comics build on |
| [../themes-and-presentation-overrides/](../themes-and-presentation-overrides/) | Theme and presentation rules that Extra Comics can override independently |
| [../rss/](../rss/) | RSS behavior for main and extra comics, including inheritance and combination rules |
