<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: AI agents and developers creating or working on feature-specific documentation.
     Purpose: Explain the folder structure and conventions for feature docs.
     Top-level docs/ is for evergreen repo-wide documentation.
     This folder is for docs scoped to a specific feature, which have a natural lifecycle. -->

# Features

This folder contains documentation scoped to specific features or product areas. Each feature gets
its own subfolder with a `README.md` index and any supporting documents.

**Top-level `docs/` is for evergreen docs that apply to the whole repo indefinitely.**
**`docs/features/` is for docs scoped to a specific feature**, which may eventually become stale,
be superseded, or be retired when the feature is.

### What belongs here

Document intent and requirements: what a feature is supposed to do, why it behaves a certain
way, and business rules or edge cases that are not obvious from reading the code.

**Do not document implementation details** such as component structure, hook call chains, or
internal data flow. The code is the source of truth for those details, and implementation docs
drift quickly.

Before writing a feature doc, ask: "Would reading the code answer this question?" If yes, skip
it. Document only what the code cannot express on its own.

## For AI Agents

Before creating any feature-specific document:

1. Check whether a folder already exists for the relevant feature. If one exists, add documents there.
2. If no folder exists, copy `_template/` to create a new folder named after the feature in kebab-case,
   then fill in `README.md` using the template before adding any other documents.
3. Never create feature-specific documents at the top level of `docs/`.
4. Apply the intent-over-implementation rule above. If the content is derivable from the code, do not create the doc.

## Folder Naming

Use short kebab-case names matching the feature or product area. Examples: `maps`, `auth`,
`billing`, `driver-dashboard`.

## Index

- [Code hooks](code-hooks/) - Expert-level Python build extensions that live in host-repo themes and are treated as a supported API, `active`
- [Comic pages and publishing](comic-pages-and-publishing/) - Core page-folder publishing rules, scheduled-post behavior, and generated page metadata, `active`
- [Extra Comics](extra-comics/) - Multi-comic site behavior built on inheritance, selective overrides, and separate comic subdirectories, `active`
- [RSS](rss/) - Feed generation rules for the main comic and Extra Comics, including inheritance and feed-combination behavior, `active`
- [Social media previews](social-media-previews/) - Open Graph-style preview metadata defaults and override points for shared links, `active`
- [Themes and presentation overrides](themes-and-presentation-overrides/) - Theme behavior, template overrides, CSS layering, and presentation asset customization, `active`
- [Transcripts](transcripts/) - Per-page transcript loading, source precedence, and language ordering behavior, `active`
- [Webring](webring/) - Optional site webring behavior driven by a shared JSON endpoint and local/site configuration, `active`
