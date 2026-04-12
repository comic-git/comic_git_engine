<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- This file is the AI entry point for this repo. It orients AI agents operating here and sets
     universal behavioral rules that apply regardless of task or workflow.
     Workflow-specific instructions belong in agent definition files, not here.
     Keep this file short — focused context produces better AI output than comprehensive context. -->

# AGENTS.md

## Project Overview

comic_git_engine is the build engine for comic_git, a static-site webcomic generator used as a submodule in comic_git repos so GitHub Actions can build and deploy creators' webcomic sites while receiving engine updates automatically.

## Behavioral Guardrails

The following actions require explicit human confirmation before proceeding, regardless of task or workflow:

- **Never push to remote** without human confirmation
- **Never merge or close MRs/PRs** without human confirmation
- **Never run destructive operations** (drop tables, delete branches, `rm -rf`, truncate data) without human confirmation
- **Never modify CI/CD configuration** without human confirmation
- **Never deploy to any environment** without human confirmation
- **Never move end-user documentation into this repo** without human confirmation; end-user docs belong in `comic_git_docs`, while this repo should keep developer-facing docs
- **Never add a new runtime dependency or environment-specific build requirement** without human confirmation; `build_site.py` must remain easy to drop into an existing `comic_git` repo and runtime dependencies should stay minimal
- **Never prepare or execute a release** without human confirmation; releases require a full manual test pass against `comic_git_dev`, complete `comic_git_docs` updates, then the normal versioning/tagging/docs/announcement workflow
- **Before modifying any file**, check `docs/decisions/` for decisions that affect it

## Key Docs

| Doc                                                      | Contents                                                      |
|----------------------------------------------------------|---------------------------------------------------------------|
| [`docs/architecture.md`](docs/architecture.md)           | System structure, components, design rationale                |
| [`docs/dev_setup.md`](docs/dev_setup.md)                 | First-time setup: dependencies, env vars, local startup       |
| [`docs/testing.md`](docs/testing.md)                     | Test frameworks, how to run and write tests                   |
| [`docs/debugging.md`](docs/debugging.md)                 | Common failures, log reading, useful commands                 |
| [`docs/gotchas.md`](docs/gotchas.md)                     | Known sharp edges and things that silently break              |
| [`docs/coding-principles.md`](docs/coding-principles.md) | How to write code that fits this repo                         |
| [`docs/contributing.md`](docs/contributing.md)           | Branching, review expectations, release workflow, AI usage    |
| [`docs/integration/`](docs/integration/)                 | External APIs and services: auth, gotchas, inaccessible specs |
| [`docs/decisions/`](docs/decisions/README.md)            | Significant decisions and the files they affect               |
| [`docs/features/`](docs/features/README.md)              | Feature-scoped documentation                                  |
| [`docs/documentation.md`](docs/documentation.md)         | Docs structure, philosophy, and where new content belongs     |
