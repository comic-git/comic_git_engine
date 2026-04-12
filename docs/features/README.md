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

Document *intent and requirements* — what a feature is supposed to do, why it behaves a certain
way, business rules and edge cases that aren't obvious from reading the code.

**Do not document implementation details** (component structure, hook call chains, data flow).
The code is the source of truth for those. Implementation docs drift quickly and will eventually
mislead more than they help.

Before writing a feature doc, ask: *"Would reading the code answer this question?"* If yes, skip
it. Document only what the code cannot express on its own.

## For AI Agents

Before creating any feature-specific document:

1. Check whether a folder already exists for the relevant feature. If one exists, add documents there.
2. If no folder exists, copy `_template/` to create a new folder named after the feature (kebab-case),
   then fill in `README.md` using the template before adding any other documents.
3. Never create feature-specific documents at the top level of `docs/`.
4. Apply the intent-over-implementation rule above. If the content is derivable from the code, do not create the doc.

## Folder Naming

Use short kebab-case names matching the feature or product area. Examples: `maps`, `video-request`,
`driver-dashboard`, `auth`, `billing`.

## Index

<!-- List feature folders here as they are created.
     Format: - [Feature name](folder-name/) — one-line summary, status -->
