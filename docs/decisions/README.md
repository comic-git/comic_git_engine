<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: AI agents and developers.
     Purpose: Explain what this folder is and how to use it.
     This file is read by the /implement and /review agents before they start work. -->

# Decisions

This folder documents significant decisions made in this codebase: architectural choices, library
selections, design tradeoffs, and anything else where understanding why matters as much as what.

The name references Chesterton's Fence: do not remove a fence before understanding why it was built.

## For AI Agents

**Before modifying any file**, search this folder for decisions that list that file in their
"Files Affected" field. If a relevant decision exists, read it before proceeding. Making a change
that contradicts an active decision requires explicit human confirmation.

To search: look for the file path or directory name in `*.md` files in this folder.

## For Developers

Create a decision doc when:
- You're making a choice where the alternative approaches are plausible
- You're making a change that future developers might want to reverse without knowing why it was made
- You're accepting a known tradeoff or limitation

Use [`_template.md`](_template.md) to create a new doc. Name files `YYYY-MM-DD-short-title.md`.

## Index

- [Code hooks as a supported expert API](2026-04-12-code-hooks-as-supported-expert-api.md) - Preserve theme hooks as a documented advanced extension surface, `active`
- [Host repo root discovery and execution context](2026-04-12-host-repo-root-discovery-and-execution-context.md) - Discover the host repo root via `your_content/` and treat host-repo execution as the real runtime context, `active`
- [Low-friction page publishing](2026-04-12-low-friction-page-publishing.md) - Reduce page-publishing effort with image and title fallbacks that match common creator workflows, `active`
- [Public output filtering and metadata exposure](2026-04-12-public-output-filtering-and-metadata-exposure.md) - Publish machine-readable metadata intentionally while keeping `!`-prefixed fields private, `active`
- [CSS layering versus template and JS overrides](2026-04-12-css-layering-vs-template-and-js-overrides.md) - Use layered CSS customization but override-based template and JS customization, `active`
- [Engine and host repo boundary](2026-04-12-engine-and-host-repo-boundary.md) - Centralize implementation in `comic_git_engine` and keep host repos thin, `active`
- [User data and configuration model](2026-04-12-user-data-and-configuration-model.md) - Keep user-facing data file-based, simple, and conservative, `active`
- [Compatibility and release policy](2026-04-12-compatibility-and-release-policy.md) - Treat patch compatibility and release discipline as product requirements, `active`
- [Built output and extension model](2026-04-12-built-output-and-extension-model.md) - Combine static output, engine-owned defaults, and host-owned extension points, `active`
