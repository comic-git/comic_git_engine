<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: New developers and AI agents that need to run the project locally.
     Purpose: Everything needed to go from a fresh clone to a running local environment.
     Be specific — exact commands, not descriptions of commands.
     If setup requires credentials or secrets, describe how to obtain them without including the values. -->

# Dev Setup

`comic_git_engine` is not intended to be run as an independent application or service. It is normally developed and tested in one of two ways:

- by running the unit tests in this repo
- by loading this repo into a `comic_git` repo such as `comic_git_dev`, usually through a symlink or git submodule, and then building that host repo locally

When running the build scripts manually, the current working directory should be the root of the host `comic_git` repo, not the root of `comic_git_engine`.

## Prerequisites

- Python 3.12 is the CI target and the safest local version to use
- A local `comic_git` repo to host this engine during manual testing, usually `comic_git_dev`
- On Windows, the ability to create symlinks or junctions if you use the symlinked workflow

Docker, databases, and external services are not required for normal local development.

## Installation

```powershell
git clone https://github.com/comic-git/comic_git_engine
cd comic_git_engine

python -m venv venv
.\venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt
```

If you need to run the TOML migration script or the full test suite, also install the migration-only dependencies:

```powershell
pip install -r requirements_migration.txt
```

If you are testing a custom theme that has Python hook dependencies, also run:

```powershell
pip install -r path/to/custom/theme/requirements.txt
```

The migration and hook dependency steps are optional for normal site builds. Keep one-off migration tooling out of `requirements.txt` so regular build installs stay minimal.

For manual site testing, load this repo into a host `comic_git` repo such as `comic_git_dev`:

- symlink or junction `comic_git_engine` into the host repo, or
- use it as the git submodule that the host repo already expects

The symlinked workflow is usually more flexible when you need to edit both repos at once.

## Environment Variables

| Variable            | Purpose                                                                                                                                              | How to get the value                                                                                                            |
|---------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| `OUTPUT_DIR`        | Controls where generated site files are written. By default, builds go into `build/`.                                                              | Usually leave unset for local builds and prefer `--output-dir` on the command line when you want a one-off override. Set it manually for workflow-style testing or set it to an empty value for legacy in-place output. |
| `GITHUB_REPOSITORY` | Lets local builds emulate the GitHub Actions environment when the host repo should keep `comic_info.ini` close to what end users receive by default. | Set this manually for local development in host repos like `comic_git_dev`, for example `ryanvilbrandt/comic_git_dev`.          |
| `INPUTS`            | Optional GitHub Actions-style multiline input string consumed by `build_site.py`.                                                                    | Usually not needed for normal local development. Set manually only when reproducing workflow behavior.                          |
| `SECRETS`           | Optional GitHub Actions-style multiline secret string consumed by `build_site.py`.                                                                   | Usually not needed for normal local development. Set manually only when reproducing workflow behavior.                          |

## Running Locally

For a quick manual build inside a host repo such as `comic_git_dev`:

```powershell
# Run from the root of the host comic_git repo
$env:GITHUB_REPOSITORY='ryanvilbrandt/comic_git_dev'
python comic_git_engine\src\build\build_site.py
```

By default, generated files are written to `build/`. If you want a different output directory:

```powershell
# Run from the root of the host comic_git repo
$env:GITHUB_REPOSITORY='ryanvilbrandt/comic_git_dev'
python comic_git_engine\src\build\build_site.py --output-dir output
```

If you want to preview pages that have future `Post date` values without deleting anything:

```powershell
# Run from the root of the host comic_git repo
$env:GITHUB_REPOSITORY='ryanvilbrandt/comic_git_dev'
python comic_git_engine\src\build\build_site.py --publish-all-comics
```

For an auto-rebuilding local preview server:

```powershell
# Run from the root of the host comic_git repo
pip install watchdog
$env:GITHUB_REPOSITORY='ryanvilbrandt/comic_git_dev'
python comic_git_engine\src\scripts\dev_server.py
```

`dev_server.py` serves the site at `http://localhost:8000` and rebuilds when `.tpl`, `.txt`, `.html`, `.md`, `.ini`, and `.toml` files change.

Do not use `--delete-scheduled-posts` during normal local development. That flag is appropriate for deployment builds because it removes future-dated page content from the published output, but locally it can delete uncommitted user data files.

## Running Tests

Run tests from the `comic_git_engine` repo root:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -t .
```

Run a single test file:

```powershell
.\venv\Scripts\python.exe -m unittest tests.integrations.test_rss
```

See [`docs/testing.md`](testing.md) for more detail on test structure and conventions.

## Common Setup Issues

- **Do not treat this repo like a standalone app.** Manual site builds should normally happen through a host `comic_git` repo such as `comic_git_dev`.
- **Run build scripts from the host repo root.** `build_site.py` and `dev_server.py` expect the current working directory to be the root of the loading `comic_git` repo.
- **Do not use `--delete-scheduled-posts` for normal local development.** It can delete future-dated comic data from the host repo. Use `--publish-all-comics` instead when you need to preview unpublished pages locally.
- **PyCharm can show the same file through multiple paths when this repo is symlinked into another repo.** If the duplicate views become confusing, mark the symlinked copy as `Excluded` in PyCharm so you only work from one visible path.
- **Be careful about setting `Comic domain` or `Comic subdirectory` directly in a host repo during local development.** For repos intended to be distributed to end users, prefer setting `GITHUB_REPOSITORY` locally instead so `comic_info.ini` stays close to the fresh-install defaults.
- **`requirements_hooks.txt` is generated during the GitHub Action, not hand-maintained.** Do not create or commit this file to the repo. If you need to install custom dependencies from a custom theme, install directly from the requirements.txt in that theme.
- If you want the old in-place build behavior for debugging or ad-hoc previewing, set `OUTPUT_DIR` to an empty value before running the build script. `--output-dir` is the cleaner option for normal one-off local overrides.
