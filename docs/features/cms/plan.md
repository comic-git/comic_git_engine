<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: Maintainers planning Decap CMS support in comic_git_engine.
     Purpose: Capture the current plan, technical direction, limits, and open questions for adding a CMS-backed editing workflow. -->

# Decap CMS Plan

## Status

Current roadmap for the browser-based CMS work. The TOML read path and deterministic migration foundation are implemented; the Decap admin surface and hosted integration remain planned.

## Summary

The goal is to add Decap CMS to `comic_git` as an optional site-wide feature that exposes a built `/admin/` interface for editing comic content over the web. `comic_git_engine` already reads TOML-backed comic and page content alongside legacy INI/TXT/JSON sources and provides deterministic local migration helpers. The remaining engine work will generate the static admin files and Decap config. Authentication and hosted orchestration may be handled by a separate GitHub App and OAuth backend, but the exact migration boundary will be decided after testing the integration.

Migration is one-way: whenever a TOML file exists, it is the source of truth and legacy files are ignored for that same logical item, regardless of whether CMS output is enabled later. The TOML format remains human-readable so creators can still edit files locally without the CMS.

## Product Goal

Allow creators to update their webcomic from the web without needing to do every content edit locally, while preserving comic_git's file-based, git-friendly model.

## Non-Goals For The First Release

- Editing templates, JavaScript, or theme hook Python through the CMS
- Turning `comic_git_engine` into a long-running server or standalone web app
- Replacing git as the source of truth
- Hiding the underlying repo structure from advanced users
- Supporting two-way synchronization between legacy files and TOML files

## Constraints From Existing Architecture

- `comic_git_engine` remains a static-site build engine loaded by host `comic_git` repos, not a standalone service.
- The host repo remains the source of truth for user content.
- Runtime dependencies should stay minimal.
- The feature must fit the existing build/deploy model and should not require users to maintain custom workflow YAML just to use the default hosted CMS backend.
- The file model must stay understandable to manual editors on Windows.

These constraints come from the existing architecture and decision docs around the engine/host boundary, the static build model, and the user-facing data model.

## Proposed User Experience

When CMS is enabled for a site:

- the engine builds an `admin/` folder into the published site
- users can open `/admin/` and edit site/comic content through Decap CMS
- uploaded comic images are stored next to the page config they belong to
- commits go directly to the repo by default, with editorial workflow available as an option

When CMS is not enabled:

- the site behaves exactly like a normal `comic_git` site
- no `admin/` output is generated
- the existing legacy content formats continue to work

## Proposed Scope For The PoC

The PoC should start broad on the content model and then narrow only where necessary for MVP.

Plan to include, then remove only if implementation cost is too high:

- main comic config
- Extra Comic config
- comic page metadata
- post text
- transcripts
- site-level social media config
- page-level social media overrides
- webring participation settings
- comic image upload and image ordering

Explicitly out of scope for the initial PoC:

- theme CSS editing
- template editing
- JavaScript editing
- hook code editing
- generated thumbnails as primary CMS-managed content

## File Format Direction

### Core Decision

CMS-managed content should move to TOML.

Initial direction:

- `comic_info.ini` -> `comic_info.toml`
- page `info.ini` -> page `info.toml`
- site-level `social_media.json` -> TOML-backed config, likely merged into `comic_info.toml`
- site webring participation settings -> TOML-backed config, likely merged into `comic_info.toml`

`webring.json` should remain a separate JSON endpoint/source-of-truth file for member data. A comic_git repo may publish that file for external callers or other comics in the webring.

### Precedence Rule

For any logical item:

- if the TOML file exists, read it exclusively
- ignore legacy INI/TXT/JSON files for that same item
- do not merge TOML and legacy fields together

This keeps the parsing model deterministic and avoids hard-to-debug mixed-mode behavior.

### Mode-Agnostic Loading

TOML loading should not depend on CMS being enabled.

If a repo has already been migrated to TOML and later disables CMS, the site should still build normally without converting files back to the legacy format. In practice this means the config/content loaders should be mode-agnostic:

- load TOML whenever the TOML file for that logical item exists
- otherwise fall back to the legacy format

This avoids any need for reverse migration logic and keeps "CMS enabled" focused on admin output and CMS-specific config, not on whether TOML files are valid engine inputs.

### Migration Rule

Migration is one-way.

The engine should own the deterministic file conversion rules through local scripts/helpers. The hosted GitHub App or another external service may orchestrate those helpers later, but should not be the only source of migration behavior.

The full migration flow should:

- convert all supported content at once
- remove the replaced legacy config/content files before the migration is considered complete
- avoid committing anything if migration fails partway through

Local tooling may support a two-step workflow: generate TOML first, let the user review it, then run explicit legacy cleanup later. Cleanup must remain opt-in because it deletes source files.

If a repo somehow ends up partially migrated anyway, the engine may tolerate that on a per-item basis if that keeps the implementation simpler, but the intended product state is a fully migrated repo.

## Proposed Config Entry Point

CMS should be enabled from the main comic config only.

Current direction:

- a CMS enable flag lives in the main comic config
- that flag affects the whole site, including Extra Comics
- Extra Comics do not get separate admin surfaces or separate CMS enable switches

The provisional config nesting is defined in [comic-info-toml-format.md](comic-info-toml-format.md). The CMS-specific subset is expected to look like:

```toml
[cms]
enabled = true
editorial_workflow = false
backend_base_url = "..."
```

Backend-related values should have engine-owned defaults in code and be overridable in config. This allows the default hosted backend to change over time without requiring every user to hand-edit their config.

## Proposed Page Content Model

### Page File

Current preferred filename:

- `info.toml`

Reason:

- it directly replaces `info.ini`
- it is clearer than `comic.toml`
- it keeps the relationship to the existing folder model obvious

### Page Schema Direction

All comic pages should share one schema, regardless of whether they belong to the main comic or an Extra Comic.

Initial direction:

```toml
title = "Page Title"
post_date = "2026-04-19"
post_text = """
Markdown text here.
"""
alt_text = "Optional hover description"
screen_reader_text = "Optional page-level screen-reader description"

[[images]]
filename = "page.png"
title = "Optional image title"
alt_text = "Optional image-specific hover description"
screen_reader_text = "Optional image-specific screen-reader description"

[transcripts]
English = "Markdown transcript here."

[social_media]
# Raw nested values for page override support in MVP
```

Likely additional fields:

- explicit thumbnail override
- tags
- page-level status fields if needed later

### Key UX Decisions

- page folder ID is user-controlled
- page folder ID should be treated as stable after creation
- page folder ID should remain path-derived rather than duplicated into `info.toml`
- title may remain optional if the engine can still derive it from image filenames where appropriate
- image ordering is explicit through `[[images]]` table order
- image fields other than `filename` remain optional so the CMS can expose
  simple and advanced editing without two data shapes
- omitted image metadata inherits engine-resolved page defaults, while explicit
  blank values suppress inheritance
- auto-discovery of page images remains legacy-mode behavior only

## Site-Level Config Direction

The simplest likely starting point is to merge CMS-relevant singleton config into the main comic config rather than keep many separate singleton files.

The local migration helper now converts both page-level content and comic-level
configuration. The provisional `comic_info.toml` schema includes the current
site-level engine settings and remains the starting point for CMS integration.

Likely areas to merge into `comic_info.toml`:

- CMS settings
- social media defaults
- webring participation settings

This should be treated as a PoC decision, not a final commitment. If the nesting becomes too awkward in Decap or too hard to maintain in engine code, splitting some parts back into separate TOML files is acceptable.

## Decap CMS Model

### Admin Output

The engine should generate `admin/` only when CMS is enabled.

Expected built files:

```text
admin/
  index.html
  config.yml
  ...
```

### Collection Direction

Likely first pass:

- file/singleton collection for main comic config
- folder collection for main comic pages
- one folder collection per Extra Comic page set

This matches the current content layout and should make the sidebar reasonably usable.

### Image Upload Direction

Uploaded comic images should live beside the page config file:

```text
your_content/comics/<page-id>/
  info.toml
  page-1.png
  page-2.png
```

Decap appears to support this pattern through folder collections with per-collection entry paths and empty relative media/public folders. That makes explicit image lists feasible without inventing a separate upload pipeline.

### Advanced Fields

If Decap handles nested objects and collapsed groups well enough, advanced fields should be hidden or collapsed by default, especially when empty.

This is a UX preference, not yet a guaranteed implementation detail.

## GitHub App / Hosted Backend Integration

This work is mostly out of scope for `comic_git_engine`, but the engine plan depends on it.

The separate repo/service is expected to handle:

- GitHub App installation
- repo authorization
- OAuth backend for Decap CMS GitHub auth
- orchestration of first-time migration from legacy files to TOML, if testing shows that belongs outside local tooling
- initial CMS enablement/config seeding
- compatibility checks against the engine version the host repo will use

The engine side must be designed so it can consume that setup cleanly while still owning deterministic local conversion behavior.

## Local Editing Direction

Local CMS usage is important, but it is not the engine's job to run a local Decap backend.

Current direction:

- document the standard local Decap workflow later
- consider adding a separate Python helper script later so local users do not need to install npm manually
- keep TOML files fully usable for normal hand-editing even without the CMS

## Technical Limitations And Risks

### 1. Dynamic Config Complexity

Generating `config.yml` dynamically is attractive because collections can reflect Extra Comics and optional features, but there is a blurry line where "dynamic" becomes hard to reason about.

Guardrail:

- generate structure from stable repo/config facts
- avoid hidden heuristics that make the CMS shape surprising

### 2. Deeply Nested Singleton Config

Merging CMS, webring, and social media data into `comic_info.toml` may simplify file layout but can make both the Decap form schema and engine parsing more complex.

This is a likely PoC pressure point.

### 3. Partial Migration

The intended flow is all-or-nothing migration, but implementation reality may lead to temporary mixed repos.

Design preference:

- tolerate partial migration only if it materially simplifies implementation
- prefer explicit failures when the mode is ambiguous

### 4. Image Management UX

The hardest part of the CMS is likely not metadata editing, but media editing:

- ordering must be preserved
- multi-image pages must stay easy to edit
- page IDs must stay stable
- file placement must remain predictable for manual editors

### 5. Social Media And Webring Schema Drift

If those formats are redesigned for TOML/CMS friendliness, the engine and end-user docs must move together. This is likely worth doing for social media defaults and webring participation settings, but `webring.json` member data should remain a separate endpoint contract.

### 6. Version Compatibility

The GitHub App must know whether a repo's configured engine version supports CMS. Otherwise it can migrate a repo into a format the current engine cannot read.

### 7. Build-Mode Ambiguity

If CMS is enabled but required CMS metadata/config is missing, the build behavior must be explicit:

- either accept partial state item-by-item
- or fail loudly

If implementation options are otherwise equal, prefer the clearer failure mode.

## Current Engine Foundation

- mode-agnostic loaders select TOML when present and otherwise fall back to legacy sources
- comic-level and page-level TOML parsers normalize into the same build-facing shapes as legacy content
- page discovery is separate from format-specific parsing
- precedence, validation, mixed-repo behavior, and deterministic migration are covered by unit tests
- migration supports both page content and comic-level configuration without requiring TOML during normal runtime builds

## Remaining Implementation Direction

### Decap PoC

- confirm Decap collection/file patterns against the real `comic_git` repo layout
- prototype generated `admin/config.yml`
- verify same-folder image upload and ordered image lists
- verify nested singleton config editing is tolerable

### Static Admin Output

- add CMS enable config
- generate `admin/index.html`
- generate `admin/config.yml`
- include only the needed collections based on the current repo/config

### GitHub App Migration Flow

- decide whether first-time migration is locally run, externally orchestrated, or both
- reuse engine-owned deterministic conversion helpers rather than duplicating migration logic in a hosted service
- convert all supported content at once
- remove replaced legacy files
- seed CMS defaults and backend config
- gate setup on compatible engine version

### Docs And Local Workflow

- write end-user CMS docs
- explain migration expectations clearly
- document local CMS editing
- optionally add a Python helper for local Decap setup later

## Recommended Early PoC Experiments

Before committing to the full build:

1. Build one real Decap folder collection that writes `info.toml` into a page folder and stores uploaded images alongside it.
2. Build one singleton collection for `comic_info.toml` with nested CMS/social/webring participation fields.
3. Verify that the Decap UI is still usable when advanced nested groups are collapsed.
4. Verify that a stable folder ID can be used as the identifier field without creating an awkward entry-creation flow.
5. Verify that explicit image ordering is easy enough for multi-image comic pages.

## Working Assumptions

- TOML remains human-readable enough to preserve the "edit locally if you want" story.
- The default hosted CMS backend is engine-owned, but overridable by advanced users.
- Editorial workflow should be optional, not the default.
- The engine should not attempt to preserve legacy write paths after migration.
- Auto-discovery belongs to legacy mode; CMS mode should be explicit.
- TOML-backed repos should continue to build even if CMS is later turned off.

## Open Questions

These are still intentionally unresolved:

- Should site-level social media defaults and webring participation config remain merged into `comic_info.toml` permanently, or only as a PoC simplification?
- Which current page-level fields should be omitted from the first CMS UI even if they remain in the TOML schema?
- How aggressively should partial migration be tolerated versus rejected?
- Does the provisional `comic_info.toml` schema stay usable once tested in the real Decap CMS UI?
- Should the local helper script for CMS setup be part of the first release or follow later?

## Notes From Decap CMS Constraints

The current plan is compatible with Decap's documented feature set:

- native `toml` collection format is supported
- folder collections support explicit identifiers and custom paths
- folder collections can store uploaded media beside entries
- file collections are appropriate for singleton config files
- `admin/index.html` plus `admin/config.yml` is the standard static admin shape

Relevant references:

- https://decapcms.org/docs/configuration-options/
- https://decapcms.org/docs/collection-folder/
- https://decapcms.org/docs/collection-file/
- https://decapcms.org/docs/install-decap-cms/
