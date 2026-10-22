# External data and preview security

Status: active. Target release: 1.1.1.

## Context and decision

The implementation review demonstrated external webring script injection and
tag-based writes outside the output directory. The maintainer approved safe
webring defaults, explicit owner trust modes, rejecting dangerous tag paths,
and loopback preview defaults for 1.1.1. These are intentional security changes
to previously permissive behavior, reviewed exceptions to patch compatibility.

- Keep global template behavior unchanged; scope autoescaping to the default
  webring template. Custom template overrides require their own escaping update.
- The owner selects `text`, `markdown`, or `unsafe_html`. External JSON cannot
  select the trust mode. Keep original names as ordinary strings for quoted
  attributes; provide `name_html` for display. Only sanitized Markdown or explicit
  unsafe HTML becomes Markup. Validate the separate link/image fields in all modes.
- Use nh3 for Markdown HTML sanitization, with a small inline tag allowlist and
  no attributes. Labels live inside links/headings, so do not allow nested links,
  image elements, or block formatting. Do not implement an HTML sanitizer ourselves.
- Abort on a broken webring by default; an explicit `omit` policy warns and omits
  the whole component. Bound response size, socket waits, body-read duration,
  and attempts. Invalid configuration always fails. No cross-build cache.
- Reject invalid tag/character paths rather than rewrite public URLs. Enforce
  resolved-path containment at the template writer as well, including symlinks.
- Preview listens on loopback unless `--listen` explicitly shares it. Require
  separate output, deny hidden paths and directory listings, and reject resolved
  paths outside that output. LAN sharing can expose unpublished preview assets.
- Pin engine runtime dependencies and their transitive dependencies. Constrain
  hook installation to those engine versions; incompatible hook requirements fail
  rather than replacing a reviewed engine dependency. Pin third-party Actions to
  verified commit refs. Preserve the existing moving engine release reference policy.

Selective asset staging and source-info exclusion remain the separate 2.0+
roadmap migration. This patch does not resolve the raw source metadata exposure.

## Files affected

- `src/integrations/webring.py`, `templates/webring.tpl`
- `src/build/content/comic_config_sources.py`, `src/build/content/page_discovery.py`
- `src/build/content/page_models.py`, `src/build/output/rendering.py`, `src/core/utils.py`
- `src/scripts/dev_server.py`, `src/build/build_site.py`
- `requirements*.txt`, `.github/workflows/`

## Validation and release boundary

Unit tests cover schema validation, trust selection, injection, failure policies,
fetch limits, tags, writer containment, and localhost HTTP serving. The e2e harness
uses a separate security fixture to exercise all modes and both layouts through
the actual build CLI, plus omission, fatal errors, and traversal rejection.
Normal build goldens remain stable for ordinary webring text.

Dependency updates require the unit and full e2e suites plus the usual manual
release pass. Version pins are not a vulnerability audit or an automatic update
mechanism. Release refs, version bumping, and publication remain separate work.
