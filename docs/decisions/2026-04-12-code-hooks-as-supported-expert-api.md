<!-- ai-agent-toolkit:managed version="1.0.0" -->

# Code hooks as a supported expert API

| Field             | Value      |
|-------------------|------------|
| **Date**          | 2026-04-12 |
| **Status**        | `active`   |
| **Supersedes**    |            |
| **Superseded by** |            |

## Context

Some comic_git customizations cannot be expressed cleanly through config, templates, or CSS alone.

comic_git already exposes Python-based code hooks through theme-owned `hooks.py` files in the host repo. These hooks are not merely an internal convenience:

- they are documented in end-user docs
- their intended purposes are documented by name
- hook-specific dependency support is documented
- `INPUTS` and `SECRETS` are documented partly to support hook-based integrations

That means the hook surface is part of the product contract for advanced users.

## Decision

Treat the existing code-hook system as a supported expert-level extension API.

- The current hook surface should be preserved carefully.
- Hooks live in the host repo so user customizations survive engine updates.
- Hooks are an advanced customization mechanism, not the preferred first-line solution for ordinary customization.
- Prefer config, templates, CSS, and other simpler extension paths when they are sufficient.
- Do not add new hook points casually. Expanding the hook surface should require a clear user-driven need.

This decision applies to the currently exposed hook model based on theme-owned `hooks.py` files and the documented hook names.

## Consequences

This preserves a powerful escape hatch for advanced users without pretending it is free to maintain.

It also means:

- refactors need to account for hook contracts, not just internal call sites
- dict shapes and data passed into hooks should be treated carefully because advanced users may depend on them
- hook-related docs and compatibility need to be considered together
- if a more declarative extension model is added later, it should likely coexist with hooks before replacing anything

## Files Affected

- `scripts/build_site.py`
- `scripts/make_requirements_hooks_file.py`
- `your_content/themes/*/scripts/hooks.py`
- `your_content/themes/*/scripts/requirements.txt`
- `docs/architecture.md`
- `docs/coding-principles.md`
- `docs/dev_setup.md`
