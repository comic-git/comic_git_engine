# TODO

## Security and reliability follow-up (2026-10-21)

Implemented for the upcoming 1.1.1 release; see the [security decision](decisions/2026-10-21-external-data-and-preview-security.md) for the contract and compatibility rationale.

* [x] Loopback preview default, explicit LAN sharing, separate output requirement, hidden-path/listing restrictions, and symlink containment.
* [x] Owner-selected escaped text, sanitized Markdown (nh3), and opt-in unsafe HTML, with scoped webring autoescaping and warnings.
* [x] Reject invalid tag/character paths with source diagnostics and constrain template writes to the output directory.
* [x] Bounded webring reads/retries, schema validation, abort default, explicit warn-and-omit, and no cache.
* [x] Pin runtime/transitive and migration dependencies and third-party Actions; constrain hook dependencies to engine pins. Preserve moving engine release refs.
* [x] Unit and real-CLI e2e regression coverage; ordinary generated-site goldens preserved.
* [ ] Complete the normal release-level manual test pass before publishing 1.1.1. Documentation is staged on `comic_git_docs` branch `release/1.1.1`.
* [ ] Selective publication/source-info exclusion remains the compatibility-sensitive [2.0+ roadmap migration](roadmap.md#selective-output-asset-staging); the raw-source privacy issue is not fixed by this patch.

## Medium Priority

* Add "Move sections to end" option for the Archive
* Look into "smart" upload to Neocities, where it only uploads changed files
* Get updated comic images from Caytlin for the showcase
* Update comic_git_showcase
* Keyboard controls https://github.com/comic-git/comic_git/issues/75
* Make 404.html path configurable
* Compile and minify CSS files

## Docs updates needed based on recent code updates

* How to use submodules
* Update "Build locally" docs to specify that the action will use whatever branch is in .gitmodules (test this)
