<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: Maintainers preparing a comic_git_engine release.
     Purpose: Provide the durable cross-repository release order, validation gates,
     and publication checklist without preserving version-specific work plans. -->

# Release Guide

Releasing `comic_git_engine` is a separate operation from merging changes into
`master`. A release changes public engine and reusable-workflow references used
by other repositories, so it requires explicit maintainer approval and a full
cross-repository validation pass.

Use a temporary plan or checklist for the specific release. This guide records
the reusable process; it is not a substitute for reviewing what changed in the
release being prepared.

## Repository Roles

| Repository              | Release role                                                      |
|-------------------------|-------------------------------------------------------------------|
| `comic_git_engine`      | Engine, reusable workflow, schemas, and release automation        |
| `e2e_tests`             | Cross-repository behavior and generated-site contracts            |
| `comic_git_dev`         | Mutable sandbox for candidate and released-ref validation         |
| `comic_git`             | Canonical user-facing starter/template repository                 |
| `comic_git_docs`        | Published end-user documentation and migration guidance           |
| `comic_git_deploy_test` | Optional host for deployment cases not covered by `comic_git_dev` |

Prepare dependent-repository changes before the engine release when useful, but
do not publish starter configuration that points at engine references that do
not exist yet. End-user documentation for unreleased behavior should likewise
remain unpublished. Open review branches or pull requests can be held until the
engine release is verified.

## 1. Define the Release

- Choose the complete `X.Y.Z` version and identify the previous exact release.
- Review the engine commits and full comparison range since that release.
- Build release notes from shipped behavior, not commit subjects alone.
- Identify every affected surface: engine behavior, reusable workflow, starter
  files and themes, end-user docs, public schemas, hooks, and generated output.
- For a minor or breaking release, prepare a prominent migration guide and test
  it against a realistically customized site. The more consequential the
  migration, the more important an in-place rehearsal is.
- Create a release-specific coverage matrix when the change set is broad. For
  each surface, name its engine tests, e2e coverage, starter work, documentation,
  and manual validation rather than relying on a single generic “tests pass” box.

A useful coverage-matrix shape is:

| Release surface | Engine tests | e2e checks | Starter/theme work | End-user docs | Manual check |
|-----------------|--------------|------------|--------------------|---------------|--------------|
| Changed behavior | Named files or suites | Named fixtures or contracts | Affected overrides | Affected pages and migration notes | A concrete scenario and expected result |

Draft release notes should lead with the user-visible summary and an important
migration link when one exists. Group the remaining notes by new features,
improvements, fixes, and breaking changes as appropriate. Record the release
date and exact comparison range during final preparation. Keep internal task
history out of the public notes; the GitHub Release is the canonical public
record, while Discord and other announcements should link back to it.

Keep temporary release plans and state logs in ignored `specs/` files. Remove
them after durable decisions and procedures have been incorporated into `docs/`.

## 2. Establish the Engine Candidate

- Run the complete engine unit suite, including release-workflow contract tests.
- Run the complete `e2e_tests` suite and its build, migration, and generated-site
  checks that apply to the release.
- Inspect generated golden changes before accepting them.
- Run the repository `/test`, `/docs`, and `/review` workflows and resolve every
  release-blocking finding.
- Confirm the final candidate is on reviewed `master`, the worktree is clean,
  and local `master` matches `origin/master`.
- Record the candidate SHA. If another commit reaches `master`, repeat the
  relevant validation against the new candidate.

Use `comic_git_dev` for the primary realistic local and remote smoke test. Point
it at the reviewed candidate, exercise the changed features, inspect its Pages
site, and record the tested SHA. Use `comic_git_deploy_test` only when a hosting
or deployment case is not adequately covered by the normal sandbox.

## 3. Prepare Documentation and the Starter

- Complete the `comic_git_docs` changes, including migration guidance and any
  advanced-user compatibility notes.
- Follow the documentation as written during at least one realistic upgrade for
  releases with meaningful migration work.
- Prepare the matching `comic_git` changes and build every affected bundled
  theme or starter variant against the engine candidate.
- Review both repositories and push their release branches when authorized, but
  hold publication or merge until the required public engine refs exist.
- If release notes must link to migration instructions before GitBook is
  published, link temporarily to the reviewed documentation branch and replace
  that link with the normal published documentation URL afterward.

## 4. Run the Final Preflight

Immediately before dispatching the release workflow, record and verify:

- the exact local and remote `master` SHA;
- clean status and passing checks in every release-critical repository;
- the targets of `latest`, the relevant moving minor refs, the previous exact
  refs, and any frozen major tag;
- absence of the new exact branch, exact tag, and GitHub Release;
- absence of another active release-workflow run;
- the prepared `comic_git`, `comic_git_docs`, `comic_git_dev`, and `e2e_tests`
  SHAs or pull requests; and
- the requested version and the expected engine/workflow selectors.

Confirm that `.github/workflows/main.yaml` still updates both version sources:

- `VERSION` in `src/build/site_builder.py`; and
- `DEFAULT_ENGINE_VERSION` in `.github/workflows/build_site.yaml`, using the
  release's major/minor value.

The reusable-workflow selector and engine selector are independent. Validate
and document both; pinning either one does not pin the other.

Obtain explicit maintainer approval before dispatching the release workflow.

## 5. Release and Verify the Engine

Dispatch `.github/workflows/main.yaml` from the reviewed `master` commit using
the complete `X.Y.Z` version. The workflow creates or advances the references
defined by the [release reference policy](decisions/2026-09-04-release-reference-policy.md)
and creates a draft GitHub Release.

After the workflow succeeds, inspect public GitHub state rather than relying on
the green workflow result alone:

- confirm `latest`, the moving minor engine branch, and moving minor workflow
  tag point to the release commit;
- confirm the exact engine branch and exact workflow tag exist and point to the
  same commit;
- confirm frozen major tags did not move;
- inspect the version constants at the exact release ref; and
- run `comic_git_dev` using both exact released selectors, then inspect its
  generated site and Pages deployment.

Do not rerun a release after an exact reference has been created. Follow the
phase-specific recovery rules in [CI/CD](cicd.md#release-workflow-safety-and-recovery)
and never move an exact reference.

## 6. Publish in Order

Once the exact-ref smoke test passes:

1. Replace or expand the draft GitHub Release body with the curated notes.
   Highlight breaking changes and link prominently to migration instructions.
2. Verify every important release-note link and publish the GitHub Release.
3. Merge and verify the prepared `comic_git_docs` update.
4. Replace any temporary documentation-branch links with their canonical
   published URLs.
5. Merge the prepared `comic_git` update and verify its workflow, generated
   site, and a clean new-starter path.
6. Announce the release last. Keep the Discord message concise, link to the
   GitHub Release as the canonical notes, and call out the migration guide when
   existing users need to take action.

## 7. Close Out

- Record any genuinely unfinished work in the roadmap or issue tracker.
- Move durable architectural reasoning into `docs/decisions/` and durable
  feature intent into `docs/features/`.
- Delete completed release plans, task lists, state snapshots, draft notes, and
  announcement scratch files from `specs/`.
- Recheck the participating repositories so the next effort starts from known
  clean branches with no dangling release work.
