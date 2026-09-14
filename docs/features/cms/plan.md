<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: Maintainers planning Decap CMS support in comic_git_engine.
     Purpose: Capture the current plan, technical direction, limits, and open questions for adding a CMS-backed editing workflow. -->

# Decap CMS Plan

## Status

The engine-side page and main-settings editing slices are implemented and
locally proven. The hosted GitHub integration and broader post-MVP CMS UX remain
planned.

## Summary

The goal is to add Decap CMS to `comic_git` as an optional site-wide feature
that exposes a built `/admin/` interface for editing comic content over the
web. The engine now generates that static admin surface for compatible
TOML-backed comic pages and the main `comic_info.toml`. Authentication and
hosted orchestration remain the responsibility of a future GitHub App and OAuth
backend.

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
- users can edit main comic/site settings through one Comic Settings page
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

The page forms support core page metadata and images. They deliberately reject
content they cannot preserve, including nonempty transcript, social-media
override, and custom `extra` tables. The Comic Settings form covers every
first-class main-config value and rejects nonempty `[legacy]` sections that it
cannot preserve. Extra Comic override configuration is not yet editable.

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

- the initial CMS presents comic-wide settings as one Comic Settings page backed
  by one `comic_info.toml` file
- common settings appear first, while less-common settings use collapsed,
  plainly labeled sections
- the provisional TOML schema follows the editing experience; it may change
  before 1.2 when its hierarchy would otherwise force confusing or unsafe UI
- page folder ID remains path-derived; it may be changed manually outside the CMS
- page folder ID should be treated as stable after creation
- page folder ID should remain path-derived rather than duplicated into `info.toml`
- CMS-managed pages require a nonblank title; broader engine title fallback behavior remains separate
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

Hands-on testing showed that a collapsed image summary using `filename`
displays the outer entry name (`info`) rather than the nested image filename.
The MVP opens image entries by default, summarizes them by explicit image Title
with a generic Image fallback, and uses compact single-line inputs for their
short text metadata rather than changing the TOML shape prematurely. A richer
custom image widget remains post-MVP work.

### Reused Metadata Suggestions

Collecting existing Storyline, Character, and Tag values is inexpensive because
CMS configuration generation already receives every built page. Decap's native
controls do not provide the intended editing behavior, however: `select` offers
a fixed option list, while `relation` searches existing collection entries but
does not accept a new arbitrary value. Relations are also awkward when values
must be gathered across the main comic and multiple Extra Comic collections.

Keep the MVP's flexible string and scalar-list inputs. A later custom creatable
combobox should use deduplicated site-wide values as suggestions while allowing
new Storylines inline; its multi-value form should act as a tag picker for
Characters and Tags. Engine-generated suggestions would refresh after the next
site build. The custom-widget investigation should decide whether that cadence
is sufficient or whether suggestions need to update from the live CMS entries
during an editing session.

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

- keep title-derived page folders as the current baseline while page identity
  and routing alternatives are evaluated
- user-facing CMS and legacy-editing guidance must warn that manually renaming a
  page folder changes its URL, page and image IDs, and generated image anchors;
  the engine does not create a redirect for the previous URL
- if Decap gains an explicit slug or page-folder control, keep that value in
  Decap-owned entry metadata rather than serializing a duplicate into
  `info.toml`
- for new entries, show a live sanitized value derived from the identifier
  field until the editor manually changes it; after a manual override, title
  edits must not silently replace the chosen slug, and the UI should offer an
  explicit way to resume automatic derivation
- treat an availability check while editing as an early warning only; repeat
  collision detection during persistence because the repository can change
  between the earlier check and publication
- include both published entries and saved editorial-workflow drafts in live and
  persistence-time collision checks. Decap currently persists and publishes one
  entry at a time; if bulk publication is added later, validate and reserve the
  complete batch of destination paths before writing any entry
- do not assume the slug control must be creation-only. First test whether a
  flat collection can use Decap's existing `meta.path` and subtree-move support
  to rename a complete comic page directory safely. If that cannot preserve all
  page files and workflows, keep the existing page location visible but
  read-only rather than offering a partial rename
- treat a page folder as one nonblank, portable filesystem and URL path segment;
  validation must reject path separators, `.` and `..`, Windows device names,
  names ending in a dot or space, control characters, Git-reserved `.git`
  equivalents, and case-insensitive or Unicode-normalization collisions, while
  allowing other spaces, Unicode, punctuation, leading dots, and mixed case
- distinguish arbitrary folders already present in the repository from folders
  created by Decap; the flat collection can edit the former, while new paths are
  always passed through Decap's slug sanitizer
- make post dates visible in page lists and investigate date-descending default
  sorting
- improve the comic-page collection grid after the MVP, potentially with page
  thumbnails and other useful at-a-glance metadata
- make Character and Tag list items expose their values without opening an
  opaque collapsed object
- add a custom image-list widget after the MVP so entries can present useful
  filenames, titles, and image context without relying on Decap's collapsed
  summary behavior
- prototype creatable suggestion controls for Storyline, Characters, and Tags
  after the MVP; they should suggest values already used throughout the site,
  accept new values inline, deduplicate suggestions case-insensitively while
  preserving display casing, and keep Characters and Tags multi-valued
- keep Images directly after Title in the edit form
- make the owning collection/path clearer for Extra Comic pages
- decide whether a polished preview is worth implementing; the first slice
  disables Decap's generic preview rather than presenting a misleading one
- keep page titles plain text unless formatted titles can be supported safely in
  page headings, archives, navigation, feeds, metadata, and identifiers

#### Page Location Hypotheses (Provisional)

| Model | Benefit | Cost or unresolved issue |
|-------|---------|--------------------------|
| Filesystem only | One source of truth and no migration; matches current engine behavior | CMS-created paths depend on title slugs, and the editor does not naturally expose title/path stability |
| Mirrored `page_folder` | Lets the engine detect that TOML and the discovered directory disagree | Adds a second representation without adding capability; cannot recover a page lost to a creation collision; must be immutable after creation |
| Independent public route | Could let storage identity remain stable while changing a page's public address and could validate route collisions after loading all pages | Adds another identity and uniqueness domain, requires broad rendering/RSS changes, and has not yet demonstrated enough user value to justify a permanent field |
| Upstream Decap change or maintained fork | Could add exact path creation, collision validation, and creation-only path controls at the layer that owns those behaviors | Upstream acceptance and timing are uncertain; a long-lived fork creates substantial release, security, and browser-compatibility maintenance |

An isolated model prototype confirms that a folder mirror can only enforce an
invariant after filesystem discovery. It also confirms that an independent
route can preserve source-derived IDs while changing and safely URL-encoding a
public path, but that concept remains a hypothesis rather than the intended
schema. Do not add either field to `info.toml` until the CMS workflow establishes
a concrete benefit.

Changing Decap itself remains in the implementation toolbox. Prefer an
upstreamable contribution developed with the Decap maintainers over a private
fork. Carry a fork only as a deliberate last resort with a narrow patch, pinned
upstream base, automated compatibility coverage, and a documented exit path;
first confirm the project's policy for AI-assisted contributions.

Maximum filesystem-level control remains available by creating or renaming the
folder outside Decap; the flat collection can discover and edit those pages.
Exact arbitrary path creation inside Decap would require custom path handling.

### Comic Settings Editor

- one main-comic settings page is backed by `your_content/comic_info.toml`
- fields are ordered and labeled for creators rather than mirroring legacy INI
  sections
- Comic Details, Website, Links, and Custom Pages are prominent; Archive,
  Navigation, Transcripts, Thumbnails, RSS, Webring, Analytics, CMS, and Engine
  settings are collapsed by default
- every accepted first-class value is represented, and unsupported legacy data
  rejects settings editing with an actionable readiness error; never let a
  partial form silently discard configuration
- Links and Custom Pages are supported because normal starter configurations
  already contain them
- preserve the proven local browser round trip in automated output coverage
- keep Extra Comic override editing deferred; reconsider it independently of
  the one-file main settings model

### Content Model Follow-ups

- separate the current hover-description concept from screen-reader alternative
  text, render the hover value through an image `title` attribute, and add a
  distinct accessible `alt` field; this is an engine-wide bug fix that should
  be handled on `master`, not hidden inside CMS UI work
- add safe round-trip support for transcripts, page social-media overrides, and
  custom `extra` data before relaxing the all-page readiness gate
- prototype singleton editing for Extra Comic configuration

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
- A blank title could produce `info.toml` and uploaded images directly in the
  collection root because the entry path uses Decap's title-derived slug. The
  generated form now explicitly requires a nonblank title before saving.
- Changing an existing title did not move its page folder, preserving
  path-derived identity.
- Quoted TOML date strings round-tripped cleanly. Native TOML dates loaded, but
  Decap exposed them as timezone-sensitive JavaScript dates, producing unwieldy
  prior-day labels in negative UTC offsets and inconsistent mixed-type sorting.
  The current CMS therefore requires quoted date-only values; future time-of-day
  work will reevaluate native date and datetime round trips explicitly.
- The page-list and collapsed-list presentation needs polish before it is
  suitable for nontechnical users.
- The existing first-class `comic_info.toml` tables mapped cleanly to native
  Decap controls, so the settings slice did not need a schema or migration
  revision. The CMS form layout remains authoritative if later UX findings do
  require a pre-release schema change.
- The settings form preserved omitted options, ordered Links, and ordered Custom
  Pages through a real Decap TOML save. CMS enablement round-tripped safely from
  true to false and back, and the resulting config completed a normal rebuild.
- Decap's generic content preview was not representative of the generated comic
  page, so it is disabled for this slice.
- A Decap 3.16.0 Playwright spike rejected the native editable-path approach.
  Nested collection metadata exposed a separate Page folder field and kept it
  out of the saved TOML, and title edits preserved the selected folder. However,
  ordinary sibling entries such as `001/info.toml` and
  `bonus-page/info.toml` disappeared from the collection because the nested
  model expects index entries to anchor its hierarchy.
- The nested path widget also applies an undocumented naming policy narrower
  than comic_git's. It accepted lowercase Unicode, hyphens, underscores, and
  `~`, but rejected uppercase letters, spaces, `.`, `+`, `&`, and `@` in the
  tested folder names.
- A second Decap 3.16.0 Playwright spike tested a serialized `page_folder`
  field in the normal flat collection with `path: "{{page_folder}}/info"`.
  Existing pages remained visible, including an existing folder named
  `Chapter 2 & Café`, and title edits left paths stable. Creating a page with
  `Chapter 3 & Café` stored that exact field value but created
  `chapter-3-café/info.toml`, confirming that field-based paths use Decap's
  slug sanitizer. Editing `page_folder` on an existing `001/info.toml` changed
  the TOML value without moving the file, so the field cannot safely remain
  editable after creation.
- A title-slug collision does not overwrite the existing `info.toml`, but stock
  Decap still reports a successful publish while writing an unusable sibling
  file. Creating a second `Same Title` produced `same-title/info-1.toml`;
  creating `A & B` beside an existing `A B` produced `a-b/info-1.toml`. The
  engine now rejects numbered `info-*.toml` and `info_*.toml` siblings with an
  actionable error, so this failure cannot silently omit the new page from a
  build. Path-aware suffixing makes the collision itself safe by creating a
  numbered sibling page folder; the engine rejection remains a fallback for
  older or unpatched Decap builds.
- Decap performs this fallback in `Backend.generateUniqueSlug` after applying
  the collection path and its native slug formatter. Public event and widget
  extension APIs run too early or do not expose the computed path and backend
  existence check, so an engine-side script would have to duplicate Decap's
  private path rules.
- A narrow Decap 3.16.2 fork prototype added a per-collection
  `slug_collision: reject` policy beside the existing suffix behavior. Focused
  Decap tests passed, and the persistent browser suite confirmed that exact and
  normalized collisions display an error without writing `info-1.toml`. This
  proves the CMS prevention UX is viable. The implementation is awaiting review
  in [decaporg/decap-cms#7992](https://github.com/decaporg/decap-cms/pull/7992),
  with user-facing documentation in
  [decaporg/decap-website#173](https://github.com/decaporg/decap-website/pull/173).
  Production configuration must not emit the option unless it is accepted
  upstream or comic_git deliberately adopts and maintains the fork.
- The generated Title field explains that its initial value determines the
  permanent page folder. It no longer tells editors to save under a temporary
  unique title because path-aware suffixing allows duplicate titles to create
  valid sibling page folders. Keep the Decap collision error itself generic for
  now; a configurable error hint is deferred unless usability testing shows the
  field guidance is insufficient.
- Decap's documented folder-collection example explicitly supports
  `path: '{{slug}}/index'` with colocated media. Suffixing a collision as
  `same-title/index-1` therefore breaks a documented entry-bundle shape, not
  just comic_git's naming convention. Treat path-aware suffix placement as a
  Decap bug fix that is separate from the configurable reject policy.
- The path-aware suffix fix applies the numeric suffix to
  the parsed built-in `slug` variable before the rest of the path, including
  filtered slug variables, while preserving whole-path suffixing for templates
  that do not reference `slug`. The full Decap test suite passes, and persistent
  browser coverage confirms that exact and normalized collisions create valid
  sibling bundles such as `same-title-1/info.toml` that rebuild successfully.
  The implementation is committed on its dedicated Decap branch; its upstream
  PR is intentionally deferred for review timing.
- Decap's source does not gate `meta.path` on enabling a nested collection. An
  existing path edit is passed to backends as `newPath`, and subtree moves
  default to enabled so colocated files can move with the entry. This may make
  an editable existing-page slug practical for a flat comic_git collection.
  It remains provisional until browser and backend tests prove that the
  metadata file, images, thumbnails, arbitrary sibling files, direct publishing,
  and editorial workflow all behave atomically and collision checks still run
  against the destination.

### Provisional Decap Patch Workflow

- Develop each generally useful Decap fix on an independent branch based on
  upstream so it can become a focused upstream PR without unrelated patches.
- Maintain a disposable comic_git integration branch in the fork that combines
  the current upstream base with the commits from every in-flight fix. Build and
  test its `packages/decap-cms/dist` output through `dev_server.py
  --decap-cms-repo` and the e2e browser suite. Do not merge the integration
  branch back into individual PR branches.
- Record the exact upstream base and independent patch-branch tip SHAs used by
  an integration build. Recreate the branch by merging those tips when upstream
  moves, rather than treating the integration branch as another source of
  changes. Keep any integration-only conflict resolution on that disposable
  branch.
- Prefer blocking production CMS support on upstream releases. If that becomes
  impractical, the fallback is an explicitly maintained comic_git Decap
  distribution published under its own package identity and immutable version,
  with the engine pinned to that exact artifact. Never load a moving fork branch
  in user sites.
- Adopting the production fallback requires a separate maintenance decision
  covering security updates, upstream synchronization, artifact publishing,
  versioning, and an exit path back to upstream Decap.

### Recommended Decap Work Sequence

1. Await review of the narrow `slug_collision` policy and documentation PRs,
   which include public documentation and identifier-neutral error wording.
2. Submit the completed path-aware suffix fix for path templates such as
   `{{slug}}/index` when its upstream PR is ready for review. Keep production
   pinned until that fix is available from a supported Decap artifact.
3. Prototype a flat-collection `meta.path` slug control with `index_file: info`.
   Test new-entry derivation and manual override separately from existing-entry
   directory renames, including normalized collisions, two colliding saved
   drafts, concurrent editor sessions, and colocated files.
4. If existing-entry renames prove complete and consistent across supported
   backends and publishing modes, design the confirmation and URL-change UX. If
   they do not, limit editing to new records before their first save and present
   persisted paths as read-only information.
5. Keep each upstreamable change independent, then combine their exact branch
   tips on the disposable comic_git integration branch for engine and browser
   testing before enabling any fork-only configuration in generated sites.

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
- Which settings controls, if any, need schema changes after the real Decap CMS
  browser round trip?
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
