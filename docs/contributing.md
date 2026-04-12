<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: Developers working in this repo (human and AI).
     Purpose: Branching strategy, review expectations, commit conventions, and guidance on working with AI.
     AGENTS.md is the AI entry point. This file is about contribution workflow. -->

# Contributing

## Branching

Small development work can happen directly on `master`.

Use a branch for:

- larger refactors
- new features
- changes that are likely to take multiple commits or need review before landing

There is no required branch naming convention.

## Commits

There is no formal commit message convention, but commit messages should be descriptive of the change they contain.

Preferred commit style:

- keep each commit limited to a single concept where practical
- avoid mixing unrelated fixes in one commit

This matters because release notes are assembled later from commit history.

## Developer Responsibility

**You are accountable for every line you merge**, regardless of whether it was written by you or by an AI assistant.

Pay particular attention to:

- **Test changes**: verify tests still describe intended behavior and were not updated just to match a regression
- **Docs changes**: verify developer docs are accurate, and be careful about when end-user docs are updated
- **Behavior changes**: confirm backward compatibility expectations before merging, especially for patch-level work

## Merge Requests

Merge requests can be merged into `master` separately from releases.

Before a change is ready to merge, it should usually have:

- relevant unit tests added or updated where practical
- manual testing in `comic_git_dev` when the change affects build behavior, generated output, or user-visible behavior
- developer-facing docs updated when the developer workflow or engine architecture changes

End-user docs in `comic_git_docs` should usually be updated close to release time, not immediately when engine changes land on `master`. That avoids publishing user-facing documentation for engine behavior that is not released yet.

If a branch includes both engine changes and matching branch updates to the end-user docs, that is useful, but not required for normal merge readiness.

## Code Review

The `comic_git` owner should review merge requests before they are merged.

Reviewers should pay extra attention to:

- backward compatibility
- generated output changes
- workflow changes
- dependency changes
- release-related changes

Patch releases should remain backward compatible. Breaking changes should be avoided in patch releases.

Major or minor version changes:

- should be rare
- should be grouped where possible
- should include migration documentation

This matters because host `comic_git` repos automatically follow patch updates by default, while major/minor updates require more deliberate user action.

## Releases

Releases are a separate step from merging to `master`.

Before a real release:

- run a full manual test pass, preferably through `comic_git_dev`
- update `comic_git_docs` completely for the released behavior
- then run the release workflow that updates version numbers, tags, and branches
- finally announce the release in Discord

## Working With AI

[`AGENTS.md`](../AGENTS.md) is the primary AI entry point for this repo. AI should also use the repo docs that have been filled in here.

### Core AI Skills

The basic workflow skills available for this repo are:

| Skill        | Purpose                                                        |
|--------------|----------------------------------------------------------------|
| `/plan`      | Turn a task into a structured plan before implementation       |
| `/implement` | Carry out an approved plan or implementation task              |
| `/test`      | Identify and add missing automated test coverage               |
| `/docs`      | Update docs affected by a change                               |
| `/review`    | Review a branch or change set for bugs, regressions, and risks |

The repo-managed skill definitions live in [`../.codex/skills/`](../.codex/skills/). To register them with a local Codex installation, run [`../.codex/skills/install-skill-junctions.ps1`](../.codex/skills/install-skill-junctions.ps1).

Good AI workflow for this repo:

1. clarify the task and any product or compatibility constraints
2. inspect the current code and tests before proposing changes
3. add or improve unit tests first where possible
4. implement changes
5. run focused tests
6. update developer docs as needed
7. plan end-user docs updates separately when the change is approaching release

AI is especially useful here for:

- refactors
- unit test expansion
- RSS/build logic changes
- developer docs maintenance

AI output always requires human review before merge.

## Related

- AI entry point: [`AGENTS.md`](../AGENTS.md)
- Setup and local workflow: [`docs/dev_setup.md`](dev_setup.md)
- Testing expectations: [`docs/testing.md`](testing.md)
- Architecture and constraints: [`docs/architecture.md`](architecture.md)
