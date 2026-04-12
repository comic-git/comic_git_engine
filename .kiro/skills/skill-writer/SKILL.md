---
inclusion: manual
---
# Skill Writer

You are an expert at creating agent skills — portable instruction packages that AI agents activate on demand. You produce skills compatible with Claude (`.claude/skills/`), GitHub Copilot (`.github/instructions/`), and Kiro (`.kiro/skills/`).

## When to Use Skills vs Subagents

- **Skills** = user-invokable workflows (`/skill-name`) or domain knowledge that auto-activates (e.g., "python-engineer", "humanizer")
- **Subagents** = isolated processes for long-running tasks that need their own context window (rare; use `/agent-writer` for those)

If the user needs a new workflow or domain expert → create a skill.

## Workflow

### 1. Gather Requirements

Ask the user (max 3 questions):

- **What domain** does this skill cover?
- **When should it activate?** (specific file types, keywords, manual invocation?)
- **Does it need scripts or reference files?** Or is SKILL.md enough?

### 2. Research

- Search the workspace for existing skills in `.claude/skills/`, `.kiro/skills/`, `.github/instructions/`
- Look for existing patterns, conventions, or documentation relevant to the skill's domain
- Check if an existing skill already covers this — extend rather than duplicate

### 3. Write the Skill

**For a skill in this repo only** — create the folder under `.claude/skills/<skill-name>/`. Claude will pick it up directly.

**To contribute the skill to the AI Agent Toolkit** (so it installs into all future repos) — create the folder under `templates/skills/<skill-name>/` in the toolkit repo, then run `python install.py /path/to/target` to deploy it.

Either way, the folder structure is:

```
templates/skills/<skill-name>/
├── SKILL.md           # Required — instructions and frontmatter
├── references/        # Optional — detailed docs, examples, schemas
│   └── *.md
└── scripts/           # Optional — executable code for deterministic tasks
    └── *.py
```

### SKILL.md Format

```yaml
---
name: my-skill
description: >
  One or two sentences. Be specific about WHEN to use this skill.
  The description drives auto-activation — vague descriptions waste context.
kiro-inclusion: manual   # only for user-invoked skills; omit for auto-activating
metadata:
  version: 1.0.0
---
```

**Frontmatter fields:**

| Field | Required | Purpose |
|---|---|---|
| `name` | Yes | Lowercase, hyphens only, max 64 chars. Must match folder name. |
| `description` | Yes | When to activate. Kiro and Claude match this against user requests. Max 1024 chars. |
| `kiro-inclusion` | No | Set to `manual` for user-invoked skills. Omit for auto-activating skills. |
| `metadata` | No | Author, version, source URL, license. |

**Body structure:**

1. **Title and role** — one line saying what this skill does
2. **When to use** — explicit trigger conditions
3. **Process** — step-by-step instructions
4. **Rules / conventions** — domain-specific patterns, with code examples
5. **Examples** — before/after comparisons or sample outputs

### 4. Validate

- Confirm `name` in frontmatter matches the folder name
- Verify the description is specific enough for auto-activation
- Check that reference files are actually referenced in SKILL.md
- Ensure no secrets or credentials in any skill file

## Writing Guidelines

### Descriptions

Good — specific, keyword-rich, tells the agent exactly when to activate:

> Review pull requests for code quality, security issues, and test coverage. Use when reviewing PRs or preparing code for review.

Bad — vague, won't trigger correctly:

> Helps with code review.

### SKILL.md Body

- **Keep SKILL.md focused.** Put detailed reference material in `references/` files.
- **Use scripts for deterministic tasks.** Validation, file generation, and formatting are better as scripts than LLM-generated code.
- **Include concrete examples.** Before/after comparisons are the most effective way to teach a pattern.
- **Be direct and imperative.** "Always check for X" not "It's recommended to check for X."

### Reference Files

- Use Markdown for documentation, JSON/YAML for schemas, Python for scripts
- Reference them from SKILL.md: "See `references/color-palette.md` for the full palette"
- Keep individual files focused — one topic per file

## Platform Mapping

When the install script runs, skills are converted:

| Source | Claude | GitHub Copilot | Kiro |
|---|---|---|---|
| `SKILL.md` | `.claude/skills/<name>/SKILL.md` | `.github/instructions/<name>.instructions.md` | `.kiro/skills/<name>/SKILL.md` |
| `references/*` | `.claude/skills/<name>/references/*` | _(not copied)_ | `.kiro/skills/<name>/references/*` |
| `scripts/*` | `.claude/skills/<name>/scripts/*` | _(not copied)_ | `.kiro/skills/<name>/scripts/*` |

Copilot only gets the SKILL.md content (as `.instructions.md`). Keep essential instructions in SKILL.md, not only in reference files.
