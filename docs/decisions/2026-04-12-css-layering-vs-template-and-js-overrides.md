<!-- ai-agent-toolkit:managed version="1.0.0" -->

# CSS layering versus template and JS overrides

| Field             | Value      |
|-------------------|------------|
| **Date**          | 2026-04-12 |
| **Status**        | `active`   |
| **Supersedes**    |            |
| **Superseded by** |            |

## Context

Most users will not replace most presentation files. The engine needs to deliver centrally maintained defaults but also allow user customization.

Different asset types support that goal differently:

- CSS can often be customized incrementally by loading additional styles afterward
- templates and JavaScript are harder to compose safely and predictably in small layers

## Decision

Use different customization models for different asset types.

- Engine CSS loads first and user theme CSS loads afterward, so users can customize styles incrementally.
- Templates are primarily override-based rather than layered.
- JavaScript is also primarily override-based rather than layered.

This is intentional. CSS is treated as the main medium for piecemeal visual customization, while templates and JS are treated as more all-or-nothing replacement points.

## Consequences

This makes common visual customization easier without forcing users to copy entire CSS files.

It also means:

- engine CSS changes can still benefit sites that only partially customize styling
- template and JS overrides need extra care because once replaced, they stop inheriting engine fixes automatically
- future refactors should not assume all asset types should share the same extension model

## Files Affected

- `default_files/css/`
- `default_files/js/`
- `templates/`
- `your_content/themes/`
- `scripts/build_site.py`
- `docs/architecture.md`
- `docs/coding-principles.md`
