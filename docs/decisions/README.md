<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: AI agents and developers.
     Purpose: Explain what this folder is and how to use it.
     This file is read by the /implement and /review agents before they start work. -->

# Decisions

This folder documents significant decisions made in this codebase — architectural choices, library
selections, design tradeoffs, and anything else where understanding *why* matters as much as *what*.

The name references Chesterton's Fence: don't remove a fence before understanding why it was built.

## For AI Agents

**Before modifying any file**, search this folder for decisions that list that file in their
"Files affected" field. If a relevant decision exists, read it before proceeding. Making a change
that contradicts an active decision requires explicit human confirmation.

To search: look for the file path or directory name in `*.md` files in this folder.

## For Developers

Create a decision doc when:
- You're making a choice where the alternative approaches are plausible
- You're making a change that future developers might want to reverse without knowing why it was made
- You're accepting a known tradeoff or limitation

Use `_template.md` to create a new doc. Name files `YYYY-MM-DD-short-title.md`.

## Index

<!-- List decision docs here as they are created, newest first.
     Format: - [Short title](filename.md) — one-line summary, status -->
