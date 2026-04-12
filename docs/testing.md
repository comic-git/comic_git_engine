<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: AI agents writing or running tests, and developers.
     Purpose: Describe the test setup, how to run tests, and how to write new ones correctly.
     An AI agent writing tests should read this before touching any test file. -->

# Testing

## Running Tests

Run tests from the `comic_git_engine` repo root.

```powershell
# Run the full test suite
$env:PYTHONPATH='scripts'
.\venv\Scripts\python.exe -m unittest

# Run tests for a specific file
$env:PYTHONPATH='scripts'
.\venv\Scripts\python.exe -m unittest tests.test_rss_feed

# Run tests matching a specific test class or test method
$env:PYTHONPATH='scripts'
.\venv\Scripts\python.exe -m unittest tests.test_build_site.TestMain

# Run with coverage
$env:PYTHONPATH='scripts'
.\venv\Scripts\python.exe -m coverage run -m unittest
.\venv\Scripts\python.exe -m coverage report -m
```

## Test Structure

Tests live in the top-level [`tests/`](../tests/) directory.

```text
tests/
  test_build_site.py  - build-site orchestration and a few remaining build helpers
  test_rss_feed.py    - RSS XML output and RSS job-selection behavior
  test_utils.py       - shared utility functions
```

Naming conventions:

- test files use `test_<module>.py`
- test classes use `Test...`
- test methods use `test_...`

This repo is in the middle of a broader modularization effort. As code is extracted from [`scripts/build_site.py`](../scripts/build_site.py), the test layout should become more granular rather than continuing to grow `test_build_site.py`.

## Testing Philosophy

### Coverage expectation

All behavioral and logic changes should be covered by automated tests where practical. Documentation-only changes, config-only changes, and generated files are excluded.

For refactors:

- add or improve unit tests first when possible
- preserve existing behavior unless there is an intentional, reviewed change
- treat missing coverage as a real risk, not as an afterthought

Manual testing in a host repo such as `comic_git_dev` is important, especially before releases, but it does not replace unit tests.

### Test type selection

Current testing in this repo is primarily unit-test-first.

Use unit tests when:

- correctness can be verified by calling a function directly
- behavior is mostly about config parsing, path handling, serialization, ordering, or transformation logic
- side effects can be isolated with mocks

Use targeted manual integration testing in a host repo such as `comic_git_dev` when:

- validating the full site build with real `your_content/` data
- checking generated HTML/RSS output in a browser or reader
- verifying that multiple engine changes still work together as expected

Use a release-level manual regression pass when:

- preparing a real `comic_git_engine` release
- confirming changes against the live manual-test workflow before users receive the update

There is interest in adding a fuller automated end-to-end regression suite later, but that is not the current default testing layer.

### Mocking strategy

Use `unittest.mock` for clear boundary isolation.

Mock these boundaries when appropriate:

- external network calls
- filesystem writes
- environment-sensitive behavior
- expensive or noisy boundary operations

Examples already in the repo include:

- `patch("builtins.open", ...)`
- `patch.dict(os.environ, ...)`
- `patch(...urlopen...)`
- patching orchestration calls in `main()` tests

Do not mock pure internal logic just to make a test easier. If behavior can be tested directly inside `comic_git_engine`, prefer testing it directly.

Reasonable rule of thumb:

- mock the boundary around the unit
- do not mock the logic inside the unit you are actually trying to verify

Internal code should remain testable even when modules are broken into smaller units. Introducing a seam for cleaner testing is fine; hiding internal behavior behind unnecessary mocks is not.

### Failing tests

A failing test is evidence of a bug regression, not a broken test. Do not update a test to match changed behavior without first verifying the code change is correct and intentional. See [`docs/contributing.md`](contributing.md) for the developer responsibility expectations around reviewing test changes.

## Writing New Tests

### File naming

- Put tests in [`tests/`](../tests/)
- Name files `test_<module>.py`
- Prefer placing tests with the module they exercise, not under a generic catch-all file, when creating new coverage for extracted modules

Examples:

- RSS logic belongs in [`tests/test_rss_feed.py`](../tests/test_rss_feed.py)
- shared utility behavior belongs in [`tests/test_utils.py`](../tests/test_utils.py)

### What to mock

Mock:

- network access
- file writes
- environment variables when behavior depends on them
- high-level orchestration collaborators when testing one orchestration layer in isolation

Do not mock:

- pure transformation logic
- serialization logic you are directly asserting on
- internal helper behavior when that helper is itself the thing under test

### Example test

Representative example from the current suite:

```python
@patch("scripts.utils.os.environ", {"GITHUB_REPOSITORY": "cvilbrandt/tamberlane"})
def test_get_comic_url_on_github(self):
    comic_info = RawConfigParser()
    comic_info.add_section("Comic Settings")
    self.assertEqual(
        ("https://cvilbrandt.github.io/tamberlane", "/tamberlane"),
        utils.get_comic_url(comic_info)
    )
```

Why this fits the repo style:

- it tests a real internal function directly
- it mocks only the environment boundary the function depends on
- it asserts on the concrete behavior, not on implementation details

## Test Categories

### Unit tests

What they cover:

- function-level and module-level behavior inside `comic_git_engine`
- config parsing
- URL/path handling
- RSS generation
- utility logic
- orchestration seams with boundary mocks

How to run:

```powershell
$env:PYTHONPATH='scripts'
.\venv\Scripts\python.exe -m unittest
```

### Manual integration testing

What it covers:

- full site builds in a host repo such as `comic_git_dev`
- template, content, and asset interactions
- RSS/manual browser validation
- real-world behavior that is awkward to verify through isolated unit tests

How to run:

- load `comic_git_engine` into a host `comic_git` repo
- build with `build_site.py` or preview with `dev_server.py`
- inspect the generated output directly

### Release-level manual regression testing

What it covers:

- final confidence before releasing changes to end users
- end-to-end verification of the changes that matter for a real engine release

Current expectation:

- run a full manual test pass, preferably through `comic_git_dev`
- update `comic_git_docs`
- only then proceed with the release workflow
