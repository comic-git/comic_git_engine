<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: AI agents and developers diagnosing failures.
     Purpose: Common failure modes, how to read logs, useful diagnostic commands, and known environment quirks.
     An AI agent hitting an unexpected error should check here before trying random fixes. -->

# Debugging

This doc is focused on local development and manual debugging.

## Reading Logs

This repo does not have a separate application log system for local development. Most useful debugging output appears directly in:

- the terminal running `build_site.py`
- the terminal running `dev_server.py`
- Python tracebacks printed to stderr

```powershell
# Run a local build and read the console output directly
$env:GITHUB_REPOSITORY='ryanvilbrandt/comic_git_dev'
python comic_git_engine\scripts\build_site.py

# Run the local preview server and watch rebuild output live
$env:GITHUB_REPOSITORY='ryanvilbrandt/comic_git_dev'
python comic_git_engine\scripts\dev_server.py
```

## Common Failures

For known coding sharp edges, see [`docs/gotchas.md`](gotchas.md).

### Missing local comic URL context

If you build locally without `Comic domain` configured in the host repo and without `GITHUB_REPOSITORY` set, URL resolution can fail with a `Comic domain` error.

Fix:

- either set `GITHUB_REPOSITORY` locally when working in a host repo like `comic_git_dev`
- or define `Comic domain` in the host repo if that repo is not meant to stay close to the end-user default setup

Example:

```powershell
$env:GITHUB_REPOSITORY='ryanvilbrandt/comic_git_dev'
python comic_git_engine\scripts\build_site.py
```

### Wrong working directory

`build_site.py` and `dev_server.py` are intended to run from the root of the host `comic_git` repo, not from the root of `comic_git_engine`.

If paths look wrong or `your_content` cannot be found, check the current working directory first.

### Future-dated pages are not showing up locally

By default, future-dated pages are not published. If you need to inspect them locally, use:

```powershell
$env:GITHUB_REPOSITORY='ryanvilbrandt/comic_git_dev'
python comic_git_engine\scripts\build_site.py --publish-all-comics
```

Do not use `--delete-scheduled-posts` for normal local debugging. That flag is for deployment-oriented builds and can delete future-dated content from the host repo.

## Useful Diagnostic Commands

```powershell
# Confirm you are in the expected host repo root
Get-Location

# Confirm the repo has the expected content source folder
Get-ChildItem your_content

# Run one focused test file while debugging a specific area
$env:PYTHONPATH='scripts'
.\venv\Scripts\python.exe -m unittest tests.test_rss_feed

# Run build orchestration tests
$env:PYTHONPATH='scripts'
.\venv\Scripts\python.exe -m unittest tests.test_build_site
```

## Environment Quirks

- Local manual builds are most useful when run through a host repo such as `comic_git_dev`, not by treating `comic_git_engine` as a standalone app.
- If `comic_git_engine` is symlinked into a host repo and both repos are open in PyCharm, the same file may appear at multiple paths.
- `OUTPUT_DIR` changes where generated files are written. If output seems to be missing, check whether it was written into a separate directory instead of the host repo root.

## Related

- Known sharp edges: see [`docs/gotchas.md`](gotchas.md)
- Test failures: see [`docs/testing.md`](testing.md)
