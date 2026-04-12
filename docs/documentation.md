<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: Developers and AI agents adding or modifying documentation.
     Purpose: Explain the docs structure, the philosophy behind it, and how to decide
     where new content belongs. Read this before creating a new doc file. -->

# Documentation Guide

## Philosophy

Docs that drift from reality are worse than no docs. The goal is accuracy over completeness.

- **Don't document what the code already makes obvious.** Document *why*, not *what*.
- **Don't duplicate.** If a doc should reference another, link to it.
- **Don't add docs for unchanged behavior.** This creates drift and noise.
- **Do document sharp edges, non-obvious decisions, and things that silently break.**

## Structure

```
docs/
├── *.md                 — Evergreen, repo-wide reference docs (setup, architecture, testing, etc.)
├── decisions/           — ADR-style records of significant choices and why they were made
├── features/            — Docs scoped to a specific feature or product area
└── integration/         — External system and API references (pure integration docs, no internal impl)
```

### Root `docs/` — Evergreen repo-wide docs

For documentation that applies to the whole repo indefinitely and doesn't have a natural expiry:
dev setup, architecture, testing conventions, coding principles, debugging, gotchas. These are
maintained continuously and should always reflect current reality.

**Add a new root-level doc when** a topic is repo-wide and doesn't fit any existing file.
Prefer adding a section to an existing doc over creating a new one.

### `docs/decisions/` — Architectural Decision Records

For choices where the *why* matters as much as the *what* — decisions a future developer might
want to reverse without knowing the cost, known tradeoffs, or anything that looks wrong but isn't.

The name references Chesterton's Fence: don't remove a fence before understanding why it was built.

**Create a decision doc when:**
- A plausible alternative approach exists and was deliberately rejected
- The change could be silently undone by someone who doesn't know the history
- You're accepting a known limitation or tradeoff

Use `_template.md`. Name files `YYYY-MM-DD-short-title.md`. Add to the index in `README.md`.

### `docs/features/` — Feature-scoped docs

For documentation tied to a specific feature or product area that has a natural lifecycle — it may
become stale, be superseded, or be retired when the feature is.

Each feature gets its own subfolder with a `README.md` index. Use the `_template/` directory to
bootstrap a new feature folder.

**What belongs here:** Content that captures *intent and requirements* — what a feature is supposed
to do, why it behaves a certain way, business rules and edge cases that aren't obvious from the
code. This is information an agent or developer can't reliably derive by reading the implementation.

**What does NOT belong here:** Implementation details — component structure, data flow, which hooks
call which functions. The code is the source of truth for those. Documenting them creates high-drift
content that will eventually mislead more than it helps.

Ask before adding a feature doc: *"Would reading the code answer this question?"* If yes, skip the
doc. If the code can't express the intent, requirements, or business reasoning — document it.

**Don't use `docs/features/` for** architectural principles, setup steps, or anything that
applies across the whole codebase.

### `docs/integration/` — External API references

For pure external system documentation — authentication patterns, endpoint references, payload
shapes — with no internal implementation detail. If a doc also covers internal hooks, services,
or components, it belongs in `docs/features/` instead.

## After Completing Work

When a feature or fix is done, the right question is not "should I preserve the plan?" — it's "what did this work produce that the code can't express on its own?"

- **Run `/docs`** to update existing docs that reflect changed behavior, interfaces, or conventions.
- **Write a `docs/decisions/` entry** if a non-obvious architectural choice was made that a future developer might want to reverse without knowing the cost. The reasoning in the plan is ephemeral; a decision doc is permanent.
- **Write a `docs/features/` entry** if there is intent, requirements, or business rules behind the feature that can't be derived from reading the implementation — applying the intent-over-implementation rule.
- **Don't preserve `specs/` files.** They are scaffolding. Once the work is merged, delete them.

## Quick Decision Guide

| Content type                                                               | Where it goes               |
|----------------------------------------------------------------------------|-----------------------------|
| How to set up the dev environment                                          | `docs/dev_setup.md`         |
| Why we made a non-obvious architectural choice                             | `docs/decisions/`           |
| Why a feature behaves a certain way (intent, requirements, business rules) | `docs/features/<feature>/`  |
| External API endpoints and auth for a third-party                          | `docs/integration/`         |
| A sharp edge or silent failure mode                                        | `docs/gotchas.md`           |
| A new failure mode or diagnostic command                                   | `docs/debugging.md`         |
| A coding convention that applies repo-wide                                 | `docs/coding-principles.md` |
| System components and data flow                                            | `docs/architecture.md`      |

## Format Conventions

All managed docs start with the `ai-agent-toolkit:managed` comment block:

```html
<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: who reads this doc
     Purpose: what this doc is for and what it covers -->
```

The audience and purpose comment is important — it tells agents (and humans) whether a doc is
relevant to their current task without them having to read the whole thing.
