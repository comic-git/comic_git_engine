<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: Human developers.
     Purpose: Human entry point for this repo. Short and navigational — links to docs, never duplicates them.
     AGENTS.md is the AI entry point; this file is for humans. -->

# comic_git_engine

`comic_git_engine` is the core engine of [comic_git](https://github.com/comic-git/comic_git), a static-site webcomic generator. It is loaded by `comic_git` repos as a submodule so GitHub Actions can build and deploy creators' webcomic sites while receiving engine updates automatically.

## Quick Start

```powershell
git clone https://github.com/comic-git/comic_git_engine
cd comic_git_engine

python -m venv venv
.\venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r scripts/requirements.txt
```

For normal manual build testing, do not run this repo as a standalone app. Load it into a host `comic_git` repo such as `comic_git_dev`, then run builds from the host repo root.

See [`docs/dev_setup.md`](docs/dev_setup.md) for the full local-development workflow, including host-repo setup, environment variables, and preview commands.

## Docs

| Doc                                                      | Contents                                                      |
|----------------------------------------------------------|---------------------------------------------------------------|
| [`docs/architecture.md`](docs/architecture.md)           | System structure and design rationale                         |
| [`docs/dev_setup.md`](docs/dev_setup.md)                 | Setup, dependencies, running locally                          |
| [`docs/testing.md`](docs/testing.md)                     | Running and writing tests                                     |
| [`docs/debugging.md`](docs/debugging.md)                 | Common failures and diagnostic commands                       |
| [`docs/gotchas.md`](docs/gotchas.md)                     | Sharp edges and things that silently break                    |
| [`docs/coding-principles.md`](docs/coding-principles.md) | Coding conventions for this repo                              |
| [`docs/contributing.md`](docs/contributing.md)           | Branching, review expectations, release workflow, AI usage    |
| [`docs/integration/`](docs/integration/)                 | External APIs and services: auth, gotchas, inaccessible specs |
| [`docs/features/`](docs/features/README.md)              | Feature-scoped documentation                                  |
| [`docs/decisions/`](docs/decisions/README.md)            | Significant past decisions                                    |
| [`docs/documentation.md`](docs/documentation.md)         | Docs structure and where things go                            |

## AI Skills

This repo has a small set of core AI skills for common development tasks.

| Skill        | What it does                                                            |
|--------------|-------------------------------------------------------------------------|
| `/plan`      | Creates a structured plan for a feature or change before implementation |
| `/implement` | Carries out an approved implementation task or plan                     |
| `/test`      | Identifies and fills automated test coverage gaps                       |
| `/docs`      | Updates documentation affected by a change                              |
| `/review`    | Reviews a change set or branch for bugs, regressions, and risks         |

Repo-local skill definitions live under [`.codex/skills/`](.codex/skills/). To register them with the PyCharm Codex integration, use [`.codex/skills/install-skill-junctions.ps1`](.codex/skills/install-skill-junctions.ps1).

See [`docs/contributing.md`](docs/contributing.md) for the recommended workflow and how these skills fit into normal development.
