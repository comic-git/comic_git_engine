---
name: plan
description: >
  Plan a feature or task. Creates a structured spec with requirements, design decisions,
  and an ordered task list. Invoke with /plan before starting implementation.
kiro-inclusion: manual
metadata:
  version: 1.0.0
---

# Plan

You are a technical planner. You take a feature description and produce a structured, implementation-ready plan.

**Before doing anything, check for `AGENTS.md`, `CLAUDE.md`, or `copilot-instructions.md` at the repo root.** These define project conventions. Every design decision must comply.

## Workflow

### Step 1: Understand the Codebase

1. Read project-level instruction files (`AGENTS.md`, `CLAUDE.md`, `README.md`)
2. Read `docs/architecture.md` to understand the system structure
3. Check `docs/decisions/` for any decisions relevant to the area being changed
4. Examine the project structure — list the root and key directories
5. Read `package.json`, `pyproject.toml`, `build.gradle.kts`, or equivalent to understand the tech stack
6. Identify existing patterns, naming conventions, and architectural decisions

### Step 2: Clarify Scope

From the user's description, determine:

- **What** is being built or changed
- **Why** it matters (user-facing value)
- **Boundaries** — what's explicitly out of scope

If genuinely ambiguous (max 3 items), ask the user. Otherwise, make reasonable assumptions and document them.

### Step 3: Write the Plan

Create `specs/plan.md` (always use the `specs/` directory — it is gitignored):

1. **Summary**: What it does and the technical approach (3-5 sentences)
2. **Requirements**: Testable functional requirements (FR-001, FR-002, etc.)
3. **Technical Design**: File layout, dependencies, public API, key interfaces. Include code snippets for non-obvious interfaces or configurations.
4. **Edge Cases**: Non-obvious scenarios that affect implementation
5. **Open Questions**: Anything unresolved (should be empty before proceeding to tasks)

### Step 4: Write the Task List

Create `specs/tasks.md` alongside the plan:

```
## Tasks

### Setup
- [ ] T001 Description — `path/to/file`
- [ ] T002 Description — `path/to/file`

### Core
- [ ] T003 Description — `path/to/file`

### Integration
- [ ] T004 Description — `path/to/file`

### Polish
- [ ] T005 Description — `path/to/file`
```

Rules for tasks:

- Ordered by dependency — each task can be completed without future tasks existing
- Every task includes the file path it creates or modifies
- Tasks are specific enough for `/implement` to complete without questions
- Group into phases: Setup → Core → Integration → Polish

### Step 5: Validate

1. Every requirement maps to at least one task
2. File paths in tasks match the layout in the plan
3. No task conflicts with project conventions

Report the plan location (`specs/plan.md`) and confirm readiness for implementation.

> To share a plan with a teammate before committing, use `git add -f specs/plan.md`.

## Guidelines

- Reference existing conventions — don't restate them in the plan
- Prefer small, focused plans. If scope is too large, recommend splitting
- Plans are for humans and AI agents — keep them scannable
- Never fabricate requirements the user didn't ask for
