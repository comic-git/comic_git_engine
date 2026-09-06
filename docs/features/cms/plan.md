<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: Maintainers planning Decap CMS support in comic_git_engine.
     Purpose: Capture the current plan, technical direction, limits, and open questions for adding a CMS-backed editing workflow. -->

# Decap CMS Plan

## Status

The engine-side page-editing vertical slice is implemented and locally proven.
The hosted GitHub integration, site-config editing, and broader CMS UX remain
planned.

## Summary

The goal is to add Decap CMS to `comic_git` as an optional site-wide feature
that exposes a built `/admin/` interface for editing comic content over the
web. The engine now generates that static admin surface for compatible
TOML-backed comic pages. Authentication and hosted orchestration remain the
responsibility of a future GitHub App and OAuth backend.

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

## Current Vertical-Slice Experience

When CMS is enabled for a site:

- the engine builds an `admin/` folder into the published site
- users can open `/admin/` and edit main and Extra Comic pages through Decap CMS
- uploaded comic images are stored next to the page config they belong to
- commits go directly to the repo by default, with editorial workflow available as an option

When CMS is not enabled:

- the site behaves exactly like a normal `comic_git` site
- no `admin/` output is generated
- the existing legacy content formats continue to work

## Proven Vertical-Slice Scope

The local browser round trip proved:

- editing existing main and Extra Comic pages
- creating image-backed and text-only pages
- uploading images beside `info.toml`
- preserving explicit image order
- changing a page title without moving its stable folder
- rebuilding the edited repo through the local engine

The first form supports core page metadata and images. It deliberately rejects
content it cannot preserve, including nonempty transcript, social-media
override, and custom `extra` tables. It does not yet edit main or Extra Comic
configuration.

Still out of scope for this slice:

- theme CSS editing
- template editing
- JavaScript editing
- hook code editing
- generated thumbnails as primary CMS-managed content
- page deletion
- CMS content previews

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

## Config Entry Point

CMS should be enabled from the main comic config only.

Current behavior:

- a CMS enable flag lives in the main comic config
- that flag affects the whole site, including Extra Comics
- Extra Comics do not get separate admin surfaces or separate CMS enable switches

The config nesting is defined in
[comic-info-toml-format.md](comic-info-toml-format.md). The CMS-specific subset
is:

```toml
[cms]
enabled = true
editorial_workflow = false
repository = "owner/repository"
branch = "master"
backend_base_url = "..."
backend_auth_endpoint = "auth"
```

The repository may instead come from `GITHUB_REPOSITORY`. Branch and auth
endpoint have engine-owned defaults; the backend base URL does not. Local
testing is selected with the runtime-only `--cms-local-backend` flag so a
developer cannot accidentally commit a deployable local-backend setting.

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

The engine generates `admin/` only when CMS is enabled.

Expected built files:

```text
admin/
  index.html
  config.yml
```

Both files carry an engine marker. Disabling CMS removes only marked generated
files during an in-place build and preserves other user-owned `admin/`
content. If `site_root` provides either generated filename, CMS output wins
with a warning.

### Collections

The first pass generates:

- one folder collection for main comic pages
- one folder collection per Extra Comic page set

This matches the current content layout and should make the sidebar reasonably usable.
Singleton comic configuration remains deferred.

### Image Upload Direction

Uploaded comic images should live beside the page config file:

```text
your_content/comics/<page-id>/
  info.toml
  page-1.png
  page-2.png
```

The local round trip confirmed this pattern through folder collections with
per-collection entry paths and empty relative media/public folders.

### Advanced Fields

Hands-on testing showed that collapsed list-item labels need further work:
Characters and Tags do not expose their values clearly, and image entries do
not reliably show their configured summary. Treat this as UI polish rather than
changing the TOML shape prematurely.

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

## Local Editing

Local CMS usage is important, but it is not the engine's job to run a local Decap backend.

Current workflow:

- run `npx decap-server` from the host repo
- run the engine development server with `--cms-local-backend`
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
- CMS settings are main-config-owned and optional
- generated admin output uses an exact Decap 3.x pin
- local proxy selection is runtime-only
- readiness validation reports all incompatible page folders before writing
- page collections cover the main comic and Extra Comics deterministically

## Remaining Implementation Direction

### Page-Editor UX

- make post dates visible in page lists and investigate date-descending default
  sorting
- investigate useful page thumbnails, potentially through an optional grid view
- make Character and Tag list items expose their values without opening an
  opaque collapsed object
- make image items reliably summarize their title, falling back to filename
- keep Images directly after Title in the edit form
- make the owning collection/path clearer for Extra Comic pages
- decide whether a polished preview is worth implementing; the first slice
  disables Decap's generic preview rather than presenting a misleading one
- keep page titles plain text unless formatted titles can be supported safely in
  page headings, archives, navigation, feeds, metadata, and identifiers

### Content Model Follow-ups

- separate the current hover-description concept from screen-reader alternative
  text, render the hover value through an image `title` attribute, and add a
  distinct accessible `alt` field; this is an engine-wide bug fix that should
  be handled on `master`, not hidden inside CMS UI work
- add safe round-trip support for transcripts, page social-media overrides, and
  custom `extra` data before relaxing the all-page readiness gate
- prototype singleton editing for main and Extra Comic configuration

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
- turn the proven local workflow into end-user guidance at release time
- optionally add a Python helper for local Decap setup later

## Findings From The First Local Round Trip

- Existing pages, new pages, image uploads, image reordering, text-only pages,
  and Extra Comic edits all worked quickly and correctly.
- Changing an existing title did not move its page folder, preserving
  path-derived identity.
- Native and quoted TOML dates round-tripped successfully when they represented
  date-only values.
- The page-list and collapsed-list presentation needs polish before it is
  suitable for nontechnical users.
- Decap's generic content preview was not representative of the generated comic
  page, so it is disabled for this slice.

## Working Assumptions

- TOML remains human-readable enough to preserve the "edit locally if you want" story.
- The default hosted CMS backend is engine-owned, but overridable by advanced users.
- Editorial workflow should be optional, not the default.
- The engine should not attempt to preserve legacy write paths after migration.
- Auto-discovery belongs to legacy mode; CMS mode should be explicit.
- TOML-backed repos should continue to build even if CMS is later turned off.
- CMS output should fail before writing if any managed page cannot be preserved.
- Production config should never be able to persist Decap's local proxy mode.

## Open Questions

These are still intentionally unresolved:

- Should site-level social media defaults and webring participation config remain merged into `comic_info.toml` permanently, or only as a PoC simplification?
- Does the provisional `comic_info.toml` schema stay usable once tested in the real Decap CMS UI?
- Should the local helper script for CMS setup be part of the first release or follow later?
- Which Decap list and collection-view features can address the proven UX
  problems without complicating the underlying TOML?
- Can a useful comic preview reuse enough of the real theme rendering to remain
  accurate, or should preview remain disabled?

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
