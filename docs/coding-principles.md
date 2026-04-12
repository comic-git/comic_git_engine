<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: AI agents writing code, and developers doing code review.
     Purpose: How to write code that fits this repo - naming conventions, patterns to follow and avoid,
     what "correct" looks like in the stack.
     AI agents should read this before writing any code. Reviewers should use it as a reference.
     Document only repo-specific additions or exceptions to general standards. -->

# Coding Principles

This doc covers repo-specific coding expectations for `comic_git_engine`.

## Naming Conventions

- Python modules use lowercase names with underscores when needed
- functions and variables use `snake_case`
- classes use `PascalCase`
- test files use `test_<module>.py`
- config option names should stay readable to end users, even when they are not Pythonic

For type hints:

- prefer built-in generics such as `list[...]` and `dict[...]`
- add explicit return type hints on new or refactored functions where practical

## Patterns to Follow

### Keep the end-user data model simple

The host repo is designed for non-technical creators. Changes should preserve the expectation that users mostly interact through:

- folders
- `.ini` files
- `.txt` files
- image files

Prefer behavior that is obvious, stable, and easy to explain in docs.

### Add tests before refactors where possible

This repo is moving toward stronger unit-test coverage. If you are about to refactor logic that already has stable behavior, add or improve tests first so the current behavior is locked down.

### Extract cohesive modules, not random helpers

When splitting code out of [`scripts/build_site.py`](../scripts/build_site.py), move related responsibilities into purpose-built modules. Do not shorten files by dumping unrelated helpers into [`scripts/utils.py`](../scripts/utils.py).

### Prefer explicit behavior over hidden magic

Defaults are good when they are understandable and easy to document. Avoid adding surprising implicit behavior, especially when it affects generated output or user-visible config semantics.

### Preserve backward compatibility, especially in patch releases

Host `comic_git` repos follow patch updates automatically. Code changes should therefore preserve existing behavior unless there is a deliberate, reviewed reason to change it.

Patch releases must never break backward compatibility.

In practice, many behavior changes in `comic_git_engine` would force users to edit their data files, templates, or config to get their builds working again. That is especially unacceptable in a patch update, because users will often receive that update automatically.

If a change would require host repos to adjust their files or workflows, it does not belong in a patch release.

## Patterns to Avoid

### Do not casually add runtime dependencies

Runtime dependencies are installed during end-user GitHub Actions builds. Any new runtime dependency adds cost and risk for every user site build.

If a dependency is only useful for maintainers or local dev tooling, it should not become required for normal engine runtime.

### Do not move end-user documentation into this repo

End-user docs belong in `comic_git_docs`. This repo should keep developer-facing documentation. It is fine to duplicate end-user concepts here when developer context needs them, but this repo should not become the primary user-doc source.

### Do not treat `comic_git_engine` like a standalone app

Code should be written with the expectation that this repo runs inside a host `comic_git` repo and reads from that repo's `your_content/` structure.

### Do not solve architectural problems by adding more global state

This codebase already has some global-state pressure through items like:

- `utils.BASE_DIRECTORY`
- cached parser/environment state in `utils.py`
- environment-variable-driven behavior

When refactoring, prefer explicit data flow over introducing additional globals.

## Stack Conventions

- Python is the primary implementation language
- `unittest` is the current automated test framework
- Jinja2 is the template layer
- markdown2 is used for Markdown conversion
- Pillow is used for image processing

Working assumptions for code structure:

- [`scripts/build_site.py`](../scripts/build_site.py) is still the main entry point
- [`scripts/rss.py`](../scripts/rss.py) owns RSS-specific logic
- [`scripts/utils.py`](../scripts/utils.py) provides shared helpers, but should not become a grab bag for unrelated logic
- reusable GitHub workflow behavior in [`.github/workflows/build_site.yaml`](../.github/workflows/build_site.yaml) is part of the product architecture, not just CI glue

## Testing Conventions

Write code so the important behavior can be tested directly.

Prefer:

- pure helper functions for transformations
- narrow orchestration seams
- boundary mocking at network/filesystem/env edges

Avoid:

- tightly coupling logic to current working directory when it can be passed in or resolved cleanly
- mixing unrelated responsibilities in one function if it makes unit testing harder
- hiding behavior in hooks or globals without a clear reason

When changing behavior:

- update or add unit tests where practical
- use manual testing in `comic_git_dev` for higher-confidence integration checks
