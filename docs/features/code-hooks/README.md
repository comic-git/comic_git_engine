<!-- ai-agent-toolkit:managed version="1.0.0" -->

# Code hooks

| Field      | Value    |
|------------|----------|
| **Status** | `active` |

## Summary

This feature provides an expert-level Python extension surface for comic_git builds.

Code hooks let advanced users run custom Python during the build process to influence page data, global template values, generated pages, and other build-time behavior that is not practical to express through config, templates, or CSS alone.

## Current State & Roadmap

The current hook system is a documented public feature, not an accidental internal escape hatch:

- hooks live in theme-owned `hooks.py` files in the host repo
- the available hook names and their purposes are documented for end users
- hook-specific third-party dependency support is also documented
- `INPUTS` and `SECRETS` exist partly to support hook-driven integrations

Important current behavior:

- code hooks are part of the supported expert feature surface
- hooks are intentionally more powerful and more flexible than declarative customization options
- hooks are not the preferred first-line customization path for ordinary site changes
- the 1.1 hook contract passes structured `ComicPage` and `ComicImage` models;
  legacy comic dictionaries and page-wide image fields are not maintained in
  parallel
- compatibility in this area matters within a release line, because advanced
  users may depend on the data passed into hooks and on when those hooks run

### Structured Hook Inputs

Existing hook names and lifecycle points are retained. Their page-bearing inputs
are now:

| Hook | Relevant 1.1 input |
|------|--------------------|
| `extra_page_info_processing` | one normalized `ComicPage` after source parsing and fallback resolution |
| `extra_comic_dict_processing` | one enriched `ComicPage`; the historical hook name remains unchanged |
| `extra_get_storylines_processing` | `list[ComicPage]` plus grouped `ArchiveEntry` projections |
| `extra_global_values` | `list[ComicPage]` |
| `build_other_pages` | `list[ComicPage]` |
| `postprocess` | the main comic's `list[ComicPage]` |

Configured source values are not duplicated on public models. Image titles, alt
text, and thumbnails exposed here are resolved values. Hooks that need source
parsing semantics belong at a source-specific boundary rather than reconstructing
inheritance from the normalized model.

`ComicImage.id` is an internal thumbnail-identity input, not a public URL or
anchor. `ComicImage` does not expose `anchor_id`; renderers derive positional
anchors from image order. Image-mode `ArchiveEntry` values expose their one-based
`image_index`; image-bearing page-mode entries expose `1`, while text-only entries
use `None`. Hook code should keep
the list order intact when positional links must remain stable.

The current roadmap direction is to harden the existing hook contracts over time rather than replace the hook system wholesale.

## Product Rules

- Code hooks should remain available as an expert-level customization mechanism.
- Config, templates, CSS, and simpler extension paths should still be preferred when they are sufficient.
- New hook points should not be added casually; expanding the hook surface should require a clear user-driven need.
- Refactors around hook-related data and lifecycle points should be reviewed carefully because advanced users may depend on those contracts.
- Future hardening should aim to clarify and stabilize the existing hook system, not silently redesign it.

## Supporting Documents

| Document | Contents |
|----------|----------|
| [../../decisions/2026-04-12-code-hooks-as-supported-expert-api.md](../../decisions/2026-04-12-code-hooks-as-supported-expert-api.md) | Why code hooks are treated as a supported expert API and not just an internal convenience |
| [../../roadmap.md](../../roadmap.md) | Future hardening direction for reviewing and tightening existing hook contracts |
| [../themes-and-presentation-overrides/](../themes-and-presentation-overrides/) | Theme ownership model that also determines where hook files live |
