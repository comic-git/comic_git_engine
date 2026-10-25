# Engine Backlog And Release Checks

This is the single index for unfinished engine work. The linked documents own the detailed requirements and procedures. Check off or remove items when completed; ordinary plans and task files in `specs/` remain temporary.

## Before The First Public CMS Release

- [ ] Run the complete engine and `e2e_tests` suites against the release candidate, inspect generated CMS output and golden changes, and perform the release-level manual pass in `comic_git_dev`. Include main Comic Settings, page editing, transcripts, social metadata, duplicate page titles, migration, and deployed login/publish. Follow [testing](../docs/testing.md), the [CMS contract](../docs/features/cms/mvp-toml-contract.md), and the [release guide](../docs/releasing.md).
- [ ] Verify the release bundle has the required path-aware Decap slug behavior and that the vendored runtime manifest matches its assets. Replace the fork bundle with an upstream release when the fix ships; follow the [runtime procedure](../docs/features/cms/updating-vendored-decap-runtime.md).
- [ ] Coordinate the public CMS instructions, migration guide, starter/template settings, and user-facing warning that renaming a page folder changes its URL and identity without generating a redirect. See the [CMS contract](../docs/features/cms/mvp-toml-contract.md#identity-and-paths) and [release guide](../docs/releasing.md).
- [ ] Confirm production CMS readiness and OAuth settings with the deployed worker before publishing the release. Local `--cms-local-backend` proof alone does not satisfy this gate; see [deployment gate](../docs/features/cms/mvp-toml-contract.md#deployment-gate).

## Deferred CMS Work

- [ ] Investigate creator-controlled page folder names separately from the title-derived default, including collision and URL behavior. See the [CMS plan](../docs/features/cms/plan.md).
- [ ] Design and test browser-safe time-of-day publishing before extending the current date-only CMS form. See [future date and time editing](../docs/features/cms/README.md#future-date-and-time-editing).
- [ ] Add safe editing for nonempty page `[extra]` data and Extra Comic override configuration, or keep them explicitly outside the CMS write contract. See [deferred TOML scope](../docs/features/cms/mvp-toml-contract.md#deferred-scope).
- [ ] Revisit page deletion, previews, folder rename controls, and custom image/tag/character/storyline widgets only with clear round-trip and identity behavior. See [deferred TOML scope](../docs/features/cms/mvp-toml-contract.md#deferred-scope).
- [ ] Consider a local CMS setup helper and later opt-in cleanup of legacy files without making migration destructive by default. See the [CMS plan](../docs/features/cms/plan.md).
- [ ] Consider webring-list editing as a separate CMS feature; the canonical `webring.json` must remain separate from `comic_info.toml`. See [comic settings format](../docs/features/cms/comic-info-toml-format.md).

## Other Planned Engine Work

- [ ] Complete the security/reliability release-level manual pass for 1.1.1. The remaining version-specific work is listed in [TODO](../docs/todo.md).
- [ ] Add an Archive option to move selected sections to the end; see [TODO](../docs/todo.md).
- [ ] Investigate changed-file-only uploads to Neocities; see [TODO](../docs/todo.md).
- [ ] Refresh comic images and the `comic_git_showcase` site; see [TODO](../docs/todo.md).
- [ ] Revisit [keyboard controls](https://github.com/comic-git/comic_git/issues/75), configurable `404.html` path, and CSS compilation/minification; see [TODO](../docs/todo.md).
- [ ] Update user guidance for submodules and verify whether local-build instructions correctly describe the branch from `.gitmodules`; see [TODO](../docs/todo.md).
- [ ] Review the architectural [roadmap](../docs/roadmap.md) before scheduling selective output asset staging, consent/storage behavior, or code-hook hardening. That document owns the detailed design of those separate workstreams.
