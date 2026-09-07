<!-- ai-agent-toolkit:managed version="1.0.0" -->

# CMS settings UX governs the comic configuration schema

| Field             | Value      |
|-------------------|------------|
| **Date**          | 2026-09-06 |
| **Status**        | `active`   |
| **Supersedes**    |            |
| **Superseded by** |            |

## Context

The provisional `comic_info.toml` schema was designed before its CMS editor.
Decap can present one file as a form with reordered, relabeled, and collapsible
fields, but native object widgets still reflect the serialized data hierarchy.
Splitting settings across files would produce separate CMS pages at the cost of
more migration, precedence, validation, and partial-state behavior.

The CMS is expected in the 1.2 release line, so this is the appropriate window
for intentional changes to the still-unreleased TOML contract.

## Decision

Use one `comic_info.toml` file and one Comic Settings page for the initial CMS.
Organize common settings first and keep less-common sections collapsed.

Treat the settings-page UX and safe round-trip behavior as authoritative when
evaluating the provisional TOML schema. Retain existing tables when they support
an approachable form and clear manual editing, but change them before 1.2 when
they force confusing controls or unsafe preservation. Update deterministic INI
migration and developer documentation with every such change; compatibility
with prerelease TOML shapes is not itself a reason to preserve poor UX.

Do not split configuration into multiple files merely to shorten the CMS form.
Reconsider a split only when testing demonstrates an independently meaningful
configuration area with a clearer ownership and lifecycle boundary.

## Consequences

- The first settings editor has one source file, one save boundary, and one
  place for manual editors to inspect.
- Friendly labels, field order, hints, and collapsed sections may differ from
  source ordering, while native widget nesting will normally follow TOML tables.
- Existing prerelease TOML test data may need regeneration as the form is
  designed.
- Any accepted value that the form cannot preserve must block settings editing
  with an actionable message rather than being silently dropped.
- A later multi-file design remains possible, but requires evidence that its UX
  benefit outweighs the additional configuration model.

## Files Affected

- `src/build/content/comic_config_sources.py`
- `src/build/migration/`
- `src/build/output/cms.py`
- `templates/cms/`
- `tests/build/content/test_comic_config_sources.py`
- `tests/build/migration/`
- `tests/build/output/test_cms.py`
- `docs/features/cms/`
- `../e2e_tests/`
