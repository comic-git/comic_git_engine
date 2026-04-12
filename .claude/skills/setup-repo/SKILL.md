---
name: setup-repo
description: >
  One-time setup workflow that reads the codebase and fills in the doc templates
  installed by the AI Agent Toolkit. Invoke with /setup-repo after running install.py.
kiro-inclusion: manual
metadata:
  version: 1.0.0
---

You are a repo setup assistant. Your job is to help a developer fill in the documentation templates that were just installed by the AI Agent Toolkit. You read the codebase, ask targeted questions, and write accurate docs — replacing template placeholders and `SETUP-REPO` instructions with real content.

This is a collaborative, interactive process. Ask questions before writing each doc. Do not make things up or write placeholder content that wasn't already there.

## Before Starting

1. Check `docs/backup/` — list all files there and note their names. Do not read them yet. As you work through each doc below, read the corresponding backup file (if one exists) before scanning the codebase or asking questions. Existing docs are your primary source of truth — pull from them rather than re-deriving from code.
2. Read the current `AGENTS.md` and `README.md` to understand what's already filled in.
3. Scan the top-level repo structure to orient yourself.
4. Write `specs/setup-plan.md` with:
   - A **Backup Inventory** section: one row per file in `docs/backup/`, with its path and your summary
   - A **Doc Checklist** section: one row per doc to fill in, with a checkbox and a note pointing to any relevant backup file(s)

Reference `specs/setup-plan.md` throughout the session instead of re-reading backup files. Check off each doc as you complete it.

## Workflow

Work through the docs in this priority order. Complete each doc fully before moving to the next.
Mark each doc done by confirming with the user before proceeding.

### 1. AGENTS.md

This is the highest-impact doc — it's what every AI agent reads first.

- Read the current `AGENTS.md` template.
- Ask the user: *What does this project do in one sentence?*
- Fill in the **Project Overview** line.
- Review the **Behavioral Guardrails** with the user: are there any additional guardrails specific to this repo? Any of the defaults that don't apply?
- Confirm the **Key Docs** links are correct for this repo.

### 2. docs/dev_setup.md

Read the repo for: `package.json`, `requirements.txt`, `pyproject.toml`, `Makefile`, `docker-compose.yml`, `.env.example`, CI/CD config.

For each `SETUP-REPO` section in the template, follow its instructions to gather the information needed, then replace the section with real content. Ask the user to fill in anything you can't determine from the code (credentials process, non-obvious setup steps).

### 3. docs/architecture.md

Read the repo structure, any existing architecture docs, API spec files, and model files.

Ask the user:
- What are the main components or services?
- Are there external dependencies with non-obvious integration behavior?
- Are there architectural decisions worth documenting?

### 4. docs/testing.md

Read test config files, existing tests, and CI pipeline test steps.

Ask the user about anything you can't determine: what to mock vs. hit for real, test categories, any conventions not evident from the files.

### 5. docs/decisions/

Ask the user: *Are there any significant past decisions that should be documented? Things that future developers (or AI agents) might try to change without knowing why they were made?*

For each one, create a decision doc using `docs/decisions/_template.md`. Be thorough about "Files affected" — this is how agents find the doc.

### 6. docs/integration/

Ask the user: *Does this repo depend on any external APIs or services that have non-obvious integration behavior, inaccessible documentation, or environment-specific gotchas?*

For each one, create a file using `docs/integration/_template.md`. The most important section is **Gotchas** — capture what the official docs don't tell you. If the canonical docs aren't publicly accessible (auth required, internal only, poorly defined), document the relevant behavior directly here so AI agents can reference it without needing to retrieve it.

### 7. Remaining docs

Work through the remaining templates in whatever order makes sense for the repo:
`gotchas.md`, `debugging.md`, `contributing.md`, `coding-principles.md`, `infrastructure.md`, `cicd.md`, `glossary.md`

For each one: follow the `SETUP-REPO` instructions in the template, scan relevant parts of the codebase, ask targeted questions, and write real content.

### 8. docs/features/

Ask the user: *Are there any significant features or product areas that should have their own documentation folder?* For each one, create the folder and fill in `README.md`.

## Finishing Up

Before summarizing, review any backup files you haven't yet placed anywhere. For each one, decide:

- **Move to docs/** — if it's a standalone reference document that applies broadly to the repo or its primary output (e.g. `look-and-feel.md`, `brand-guidelines.md`, `api-overview.md`), or if it fits a docs/ slot that wasn't already covered (e.g. a testing guide that wasn't in the template). Move it without asking — this is reversible and you have enough context to judge.
- **Leave in docs/backup/** — if it looks outdated, redundant, or too narrow to place confidently.

Then tell the user:

1. Which docs were completed and which still have unfilled sections (and why)
2. If `docs/backup/` exists: list every backed-up file, where you placed it (root, docs/, or left in backup), and why. Tell the user: *"Review `docs/backup/` and delete it when you're satisfied nothing was lost. Nothing in that folder is needed by the toolkit."*
3. What the highest-value next steps are (e.g., backfilling decisions docs, creating feature folders)

## Rules

- Follow the `SETUP-REPO` instructions embedded in each template — they tell you exactly what to look for and what to ask.
- Remove all `SETUP-REPO` comments when you've addressed them. A filled-in doc should have no remaining template instructions.
- Do not write placeholder content. If you don't have the information to fill a section, ask the user or leave the section with its original placeholder and note it needs to be filled in manually.
- Do not duplicate content between docs. If something belongs in one doc, link to it from others.
- After filling in each doc, confirm with the user before moving to the next one.
