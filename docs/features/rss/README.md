<!-- ai-agent-toolkit:managed version="1.0.0" -->

# RSS

| Field      | Value    |
|------------|----------|
| **Status** | `active` |

## Summary

This feature covers RSS feed generation for comic_git sites, including both the main comic and Extra Comics.

It defines when feeds are built, where feed files are written, how Extra Comics inherit or override RSS settings, and how feed item titles and links are determined.

## Current State & Roadmap

The current RSS model is per-comic, with inheritance from the main comic plus a selective combination rule for Extra Comics:

- the main comic can build a root `feed.xml`
- an Extra Comic inherits the main comic's RSS settings unless it overrides them
- an Extra Comic normally gets its own `<extra>/feed.xml`
- if `Combine with Main RSS Feed = True`, that Extra Comic's posts appear in the main comic's root feed instead of getting a separate feed file

Important current behavior:

- `Build RSS feed` controls whether a comic participates in RSS at all
- `Combine with Main RSS Feed` applies only to Extra Comics, but may be inherited from the main comic as a default
- `RSS title format` follows the comic that owns the post, not the feed file where that post appears
- feed metadata has built-in defaults for language and channel image, with `Description` falling back to the comic's normal description
- feed output paths are part of the published site contract

This feature is stable in behavior, but it depends on the current output model. A future output-directory-first migration may change how feed files and feed-referenced assets are staged, even if the user-facing feed rules remain the same.

## Product Rules

- RSS should remain opt-in per comic.
- Extra Comics should behave independently by default, with combination into the main feed requiring an explicit setting.
- Inherited RSS settings should reduce setup work, but Extra Comics must be able to override them individually.
- Title formatting should belong to the comic that owns the content, not to the feed file that happens to contain it.
- Refactors in this area should be reviewed carefully because feed paths, item URLs, and feed inclusion rules are externally consumed behavior.

## Supporting Documents

| Document | Contents |
|----------|----------|
| [../extra-comics/](../extra-comics/) | Multi-comic inheritance and override behavior that RSS builds on |
| [../../decisions/2026-04-12-built-output-and-extension-model.md](../../decisions/2026-04-12-built-output-and-extension-model.md) | Why generated RSS output is treated as part of the product contract and why per-comic title behavior matters |
| [../../roadmap.md](../../roadmap.md) | Future output-structure changes that may affect how feed files are staged or published |
