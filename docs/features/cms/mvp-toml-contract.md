<!-- ai-agent-toolkit:managed version="1.0.0" -->

# CMS MVP TOML Contract

## Purpose

This document defines the source-data boundary for the implemented Decap CMS
vertical slice. It separates TOML that the engine can build from TOML that the
current CMS can open and save without loss. It is a maintainer contract, not
end-user migration guidance.

CMS generation is all-or-nothing. Before the engine writes `admin/`, it checks
the main configuration and every main or Extra Comic page folder. A compatible
repo may use the CMS; an incompatible repo still builds normally outside CMS
mode.

## Compatibility Matrix

| Source shape                                                                                     | Normal engine build |   CMS MVP | Notes                                                                                                                                                  |
|--------------------------------------------------------------------------------------------------|--------------------:|----------:|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| Main `comic_info.toml` first-class fields                                                        |                 Yes |       Yes | The Comic Settings collection represents every currently accepted first-class main-config field, including ordered `[[links]]` and `[[pages]]`.        |
| Main `[legacy]` with no values                                                                   |                 Yes |       Yes | Empty compatibility tables are preserved.                                                                                                              |
| Main nonempty `[legacy]`                                                                         |                 Yes |        No | The form cannot round-trip arbitrary legacy keys.                                                                                                      |
| Extra Comic `comic_info.toml` overrides                                                          |                 Yes | No editor | Extra Comic pages are editable, but their override config is deferred.                                                                                 |
| Page `title`, quoted date-only `post_date`, `post_text`, page metadata, and ordered `[[images]]` |                 Yes |       Yes | This is the page editor's first-class data shape. Images may be omitted for a text-only post.                                                          |
| Image `filename`, `title`, `alt_text`, `screen_reader_text`, and `thumbnail`                     |                 Yes |       Yes | Optional image fields preserve omission and explicit blank values.                                                                                     |
| Quoted ISO page timestamps                                                                       |                 Yes |        No | The CMS currently accepts only `YYYY-MM-DD` to avoid timezone conversion and mixed-type sorting.                                                       |
| Native TOML page dates or datetimes                                                              |                 Yes |        No | Valid engine input, deliberately excluded from browser editing.                                                                                        |
| Page `[transcripts]`, `[social_media]`, or `[extra]` with no values                              |                 Yes |       Yes | Empty tables do not contain data that could be lost.                                                                                                   |
| Page `[transcripts]` or `[social_media]` with nonblank string keys and string values             |                 Yes |       Yes | Transcript values use Decap's Rich Text/Markdown editor; metadata maps support arbitrary external keys, including quoted TOML keys such as `og:title`. |
| Nonempty page `[extra]`                                                                          |                 Yes |        No | Keep arbitrary custom data manually managed until the form can preserve its shape.                                                                     |
| Page `[transcripts]` or `[social_media]` with blank keys or non-string values                    |                 Yes |        No | The map widgets deliberately support only simple string-keyed data.                                                                                    |
| Legacy page `info.ini` and companion legacy files                                                |                 Yes |        No | Migrate the page to `info.toml` before enabling CMS.                                                                                                   |
| A page folder without `info.toml`                                                                |    Legacy-dependent |        No | Every discovered page folder must be a compatible TOML page.                                                                                           |

The detailed source schemas remain in
[comic-info-toml-format.md](comic-info-toml-format.md) and
[page-toml-format.md](page-toml-format.md). This matrix intentionally records
the narrower CMS write contract without weakening the engine read contract.

## Identity And Paths

The page folder remains the source-derived page identity. Decap creates a new
folder from the initial title slug and keeps that folder when the title changes.
The folder is not duplicated in `info.toml`.

Manual folder renames remain supported outside the CMS, but change the page
URL, page and image IDs, and image anchors. The engine does not generate a
redirect from the old URL. Duplicate title slugs require Decap's path-aware
collision behavior: a new entry must become a sibling bundle such as
`same-title-1/info.toml`, never `same-title/info-1.toml`.

## Deployment Gate

The future OAuth service must treat this contract as a precondition rather than
trying to repair repositories while publishing. It may offer deterministic
migration, but it must not enable production CMS for a repo until all of these
are true:

- the configured engine version supports TOML-backed CMS output;
- `validate_cms_inputs` accepts the main config and every page root;
- the production Decap bundle contains path-aware slug suffixing, either from
  an upstream release or an explicitly maintained immutable comic_git fork
  artifact; and
- production backend settings are valid for the chosen OAuth service.

The runtime-only `--cms-local-backend` flag is for local proof work only. It
does not change source files or satisfy the production authentication gate.

## Deferred Scope

- time-of-day page publishing and a browser-safe timestamp representation;
- custom `extra` fields;
- Extra Comic override configuration;
- page deletion, previews, and folder rename controls;
- custom image, tag, character, and storyline widgets; and
- the hosted OAuth service and first-time migration UX.

## Verification

The contract is enforced at three levels:

| Coverage                    | Purpose                                                                                            |
|-----------------------------|----------------------------------------------------------------------------------------------------|
| Engine readiness unit tests | Reject every incompatible source shape before admin files are written.                             |
| Generated-site CMS contract | Confirm production admin output matches the supported main-settings and page schema.               |
| Playwright CMS fixture      | Open and save representative supported page data through Decap, then rebuild with the real engine. |
