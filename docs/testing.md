<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: AI agents writing or running tests, and developers.
     Purpose: Describe the test setup, how to run tests, and how to write new ones correctly.
     An AI agent writing tests should read this before touching any test file. -->

# Testing

## Running Tests

Run tests from the `comic_git_engine` repo root.

The `tests` package adds `src` to `sys.path`, so normal unittest commands do not need a `PYTHONPATH` prefix.

Install both core and migration-only dependencies before running the full suite:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m pip install -r requirements_migration.txt
```

```powershell
# Run the full test suite
.\venv\Scripts\python.exe -m unittest discover -s tests -t .

# Run tests for a specific file
.\venv\Scripts\python.exe -m unittest tests.integrations.test_rss

# Run a specific test class or test method
.\venv\Scripts\python.exe -m unittest tests.build.test_build_site.TestMain
.\venv\Scripts\python.exe -m unittest tests.scripts.test_entrypoints.TestEntrypoints.test_build_site_can_be_run_directly_by_path

# Run with coverage
.\venv\Scripts\python.exe -m coverage run -m unittest discover -s tests -t .
.\venv\Scripts\python.exe -m coverage report -m
```

## Test Structure

Tests live in the top-level [`tests/`](../tests/) directory.

```text
tests/
  build/
    test_build_site.py         - top-level build orchestration in `main()`
    test_site_builder.py       - per-comic pipeline orchestration and shared page projections
    content/
      test_archive_config.py   - archive entry-mode compatibility and defaults
      test_comic_config_sources.py - comic-level INI/TOML source parsing and conversion
      test_comic_data.py       - structured comic page enrichment
      test_loaders.py          - source selection and TOML-over-INI precedence
      test_page_discovery.py   - page discovery, scheduling, source resolution, and validation
      test_page_models.py      - page/image identity, navigation, and fallback rules
      test_page_metadata.py    - versioned public metadata serialization and schema artifact
      test_page_sources.py     - page-level INI/TOML parsing and normalization
      test_site_config.py      - config parsing and extra-comic config merging
      test_transcripts.py      - transcript loading and ordering
    migration/
      test_toml_migration.py   - deterministic legacy-to-TOML conversion
    output/
      test_images.py           - page/image thumbnail resolution and generation behavior
      test_rendering.py        - template/page-writing orchestration
      test_site_output.py      - output cleanup and site_root/output copying
  core/
    test_logging_config.py     - build logging configuration
    test_utils.py              - shared utility functions
  integrations/
    test_rss.py                - RSS XML output and RSS job-selection behavior
    test_webring.py            - webring data loading and validation
  scripts/
    test_entrypoints.py        - direct script execution by file path
```

Naming conventions:

- test files use `test_<module>.py`
- test classes use `Test...`
- test methods use `test_...`

Keep [`tests/build/test_build_site.py`](../tests/build/test_build_site.py) focused on `main()` and other top-level orchestration seams. Per-comic orchestration belongs in [`tests/build/test_site_builder.py`](../tests/build/test_site_builder.py); lower-level behavior should usually be covered in the module-specific test file that matches the module being changed.

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

Use automated end-to-end tests in `e2e_tests` (usually at `../e2e_tests`) when:

- the risk depends on realistic host-repo execution
- behavior only appears when multiple engine subsystems run together across a full build
- validating entrypoint, submodule, or host-layout behavior that unit imports cannot catch
- checking generated site output that depends on real files, templates, assets, and config together
- validating generated `page_info_list.json` instances with the JSON Schema
  deployed by the same build
- preventing recurrence of a bug that escaped unit tests because it only appeared in full-build context

Do not add an end-to-end case by default. First ask whether the behavior can be covered with focused unit tests in this repo. Every new end-to-end test should have a clear reason why unit tests alone are insufficient, and the underlying engine logic should still get unit coverage where practical.

Because `e2e_tests` is a separate repo, usually located next to this repo at `../e2e_tests`, do not modify it unless the current task explicitly asks for cross-repo test updates or the user confirms that e2e harness changes are in scope.

Before finishing a behavioral engine change, explicitly report one of:

- `e2e_tests updated` with a short reason
- `e2e_tests not needed` with the reason unit coverage is sufficient
- `e2e_tests recommended but not changed` with the blocker or required human decision

Use a release-level manual regression pass when:

- preparing a real `comic_git_engine` release
- confirming changes against the live manual-test workflow before users receive the update

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

Put tests in [`tests/`](../tests/) and name files `test_<module>.py`.

Mirror the runtime module name rather than adding behavior to a generic catch-all file. Examples from this repo:

- [`src/core/utils.py`](../src/core/utils.py) -> [`tests/core/test_utils.py`](../tests/core/test_utils.py)
- [`src/integrations/rss.py`](../src/integrations/rss.py) -> [`tests/integrations/test_rss.py`](../tests/integrations/test_rss.py)
- [`src/build/output/site_output.py`](../src/build/output/site_output.py) -> [`tests/build/output/test_site_output.py`](../tests/build/output/test_site_output.py)

For extracted modules, prefer the module-specific test file over adding more coverage to [`tests/build/test_build_site.py`](../tests/build/test_build_site.py). Directly runnable entrypoints can share [`tests/scripts/test_entrypoints.py`](../tests/scripts/test_entrypoints.py) when the behavior under test is "does this script run correctly by path?"

### Test class structure

Tests are organized into `unittest.TestCase` classes, usually one class per logical unit or feature area under test, such as `TestGetComicUrl`, `TestRssFeed`, `TestSiteOutput`, or `TestEntrypoints`.

This layout makes it easy to:

- keep helper methods close to the tests that use them
- apply class-level `@patch(...)` decorators when many tests share the same defaults
- use `setUp()` or `setUpClass()` for shared state that should be reset before each test or once per class

Example patterns already in this repo include:

- helper builders like `make_comic_info()` in [`tests/build/test_build_site.py`](../tests/build/test_build_site.py)
- `setUpClass()` for shared RSS config in [`tests/integrations/test_rss.py`](../tests/integrations/test_rss.py)

If a test class needs to reset module-level state before each test, do that in `setUp()`.

### Module under test constant

When a test file patches the same runtime module repeatedly, define a `MUT` constant at the top of the file and build patch targets from it.

```python
MUT = "build.build_site."

@patch(MUT + "load_main_comic_info")
@patch(MUT + "utils.get_comic_url", return_value=(COMIC_URL, "/comic_git_dev"))
class TestMain(TestCase):
    ...
```

This keeps patch targets short and makes it obvious which module is under test. It is especially helpful in orchestration-heavy files like [`tests/build/test_build_site.py`](../tests/build/test_build_site.py), where the same module path is repeated many times.

### Patch decorator placement

Use `@patch` at two levels:

- class-level for mocks that should apply to every test in the class with a sensible default
- method-level for mocks whose `return_value` or `side_effect` varies meaningfully between tests

```python
MUT = "build.build_site."

@patch(MUT + "print_processing_times")
@patch(MUT + "checkpoint")
class TestMain(TestCase):

    @patch(MUT + "load_main_comic_info")
    @patch(MUT + "get_extra_comics_list", return_value=[])
    def test_main_builds_rss_feed_job_from_main_comic(self, *_mocks):
        ...
```

Patch where the code looks up the symbol, not where the symbol was originally defined. For example:

- patch `build.build_site.load_main_comic_info` when testing [`build.build_site`](../src/build/build_site.py)
- patch `build.output.site_output.shutil.copytree` when testing [`build.output.site_output`](../src/build/output/site_output.py)
- patch `core.utils.os.environ` or use `patch.dict(os.environ, ...)` when testing environment-sensitive helpers in [`core.utils`](../src/core/utils.py)

If you patch the wrong import path, the real dependency will still run.

### Mock access via a helper dict

Once a test mixes class-level and method-level patches, long positional mock argument lists become hard to read. Prefer `def test_x(self, *_mocks)` over a large list of named positional arguments, then access mocks by name through a helper dict.

The template guidance for this repo uses a `get_mock_dict` helper. `comic_git_engine` does not currently ship a shared one, so if a new test file grows large enough to need this pattern, add a small helper in that file or a shared helper under `tests/` before adopting it broadly.

Illustrative pattern:

```python
def get_mock_dict(mocks):
    return {mock._mock_name: mock for mock in mocks}


MUT = "build.build_site."

@patch(MUT + "load_main_comic_info")
class TestMain(TestCase):

    @patch(MUT + "get_extra_comics_list", return_value=[])
    def test_main_builds_rss_feed_job_from_main_comic(self, *_mocks):
        m = get_mock_dict(_mocks)
        m["load_main_comic_info"].return_value = self.make_comic_info()
        m["get_extra_comics_list"].assert_not_called()
```

Mock names come from the last component of the patch target. If two patches would produce the same name, they will collide in the dict; in that case use distinct patch targets or access one of them positionally.

### Log assertions

`caplog` is a pytest fixture and does not apply inside `unittest.TestCase` methods. If a test in this repo needs to assert on logging output, use `assertLogs` instead.

```python
with self.assertLogs("build.build_site", level=logging.WARNING) as cm:
    build_site.main()
assert any("expected message" in msg for msg in cm.output)

with self.assertLogs("build.build_site", level=logging.DEBUG) as cm:
    build_site.main()
assert not any("unexpected message" in msg for msg in cm.output)
```

`assertLogs` requires at least one record at or above the capture level. If the code under test emits debug logs unconditionally, capturing at `DEBUG` is the safe way to assert that a warning was not emitted.

### Writing script-entrypoint tests

For directly runnable scripts under `src/build/` and `src/scripts/`, prefer subprocess-based tests that execute the file by path from a temporary working directory.

See [`tests/scripts/test_entrypoints.py`](../tests/scripts/test_entrypoints.py) for the current pattern:

- run `subprocess.run([sys.executable, script_path, ...])`
- clear `PYTHONPATH` in the subprocess environment
- assert that the script does not fail with `ModuleNotFoundError`
- assert on the real CLI output or failure message

These tests cover the host-repo runtime path that unit imports alone will miss.

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
.\venv\Scripts\python.exe -m unittest discover -s tests -t .
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

### Automated end-to-end tests

What they cover:

- full-build regressions that require realistic host-repo execution
- interactions among engine subsystems that are not meaningful as isolated unit tests
- generated-output regressions where a focused golden case is justified

Where they live:

- `e2e_tests`, usually at `../e2e_tests`

Current expectation:

- keep most behavior covered by unit tests in this repo
- add e2e cases only when the integration risk is real and documented
- do not modify `e2e_tests` without explicit task scope or user confirmation

### Release-level manual regression testing

What it covers:

- final confidence before releasing changes to end users
- end-to-end verification of the changes that matter for a real engine release

Current expectation:

- run a full manual test pass, preferably through `comic_git_dev`
- update `comic_git_docs`
- only then proceed with the release workflow
