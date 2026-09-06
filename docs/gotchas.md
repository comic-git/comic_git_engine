<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: AI agents and developers about to modify the codebase.
     Purpose: Known sharp edges - brittle areas, non-obvious breakage, things that silently go wrong.
     The /implement and /review agents read this before and after making changes.
     Keep this list short. A long list is a signal things need fixing, not just documenting. -->

# Gotchas

### Run build scripts from the host repo root

[`src/build/build_site.py`](../src/build/build_site.py) and [`src/scripts/dev_server.py`](../src/scripts/dev_server.py) are meant to be run with the current working directory set to the root of the host `comic_git` repo, not the root of `comic_git_engine`.

If you run them from the wrong directory, project-root discovery and file loading can fail in confusing ways. When doing manual builds, always start from the loading repo.

### PyCharm can show the same file through multiple paths

When `comic_git_engine` is symlinked into a host repo and both repos are open in the same PyCharm project, the same physical file can appear at multiple paths.

This can make it look like there are duplicated files or mismatched edits when it is really the same file being reached through different repo views. If this becomes confusing, mark the symlinked copy as `Excluded` in PyCharm so you only work from one visible path.

### CMS enablement validates every comic page

The CMS is site-wide. Enabling it from the main `comic_info.toml` also manages
Extra Comic page roots, and the engine writes no admin files unless every page
folder is safe for the current form to round-trip.

A legacy `info.ini`, missing or invalid `info.toml`, blank title, timestamp
`post_date`, or nonempty `[transcripts]`, `[social_media]`, or `[extra]`
table blocks CMS generation with an aggregate error. These remain valid in
ordinary non-CMS builds; the restriction protects content from a lossy CMS
save.

The `--cms-local-backend` option changes only backend rendering for the current
process. It does not bypass readiness and should never be represented as a
committed config value.
