<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: Maintainers. Purpose: Explain the compatibility boundary for selective staging. -->

# Opt-in selective content staging

Date: 2026-11-07. Status: active. Target release: 1.1.1.

## Context

Legacy deployment deletes future page folders before copying your_content. That
works in disposable Actions checkouts but makes local deployment awkward. Local
SFTP previously copied the source tree into a temporary project to accommodate
that deletion, changing the working directory and hiding host files from hooks.

## Decision

- Offer selective copying as an opt-in, site-wide policy; preserve legacy defaults
  and allow a one-invocation override of configured selection.
- Let discovery select pages once. The output layer copies whole selected page
  folders, not just assets it can discover references to. Managed comics roots
  contain only eligible page folders; loose files there are omitted.
- Prune all configured Extra Comic comics roots from auxiliary copying, including
  nested paths. Unconfigured directories remain ordinary content.
- Skip incomplete required metadata with diagnostics only in selective mode.
  Malformed syntax, invalid supplied values, and unsafe/missing assets still fail.
- Keep thumbnail generation in source folders before copying. Creators can commit
  this cache; selective builds prevent scheduled-source deletion, not all writes.
- Exclude hidden output by default in selective mode, support configured include-all,
  and let explicit exact-path allowlists take precedence. Preserve SFTP's final
  hidden-path filter after root copying and hooks.
- Use the actual host working directory for native local SFTP, with temporary
  output and selective copying enabled. Leave credentials and transfer behavior
  at their existing boundary.

## Consequences

Existing builds do not silently change publication behavior. Creators can test a
future default without losing arbitrary supporting assets or changing asset URLs.
Selected source info files are still public; this does not fix raw metadata
privacy. Link aliases are unsupported in selective source content. A default
switch and source-info exclusion remain separate compatibility decisions.

## Files affected

- src/build/build_site.py, src/build/site_builder.py
- src/build/content/{page_discovery,page_sources,loaders,comic_config_sources}.py
- src/build/output/{content_staging,site_output}.py
- src/scripts/{dev_server,deploy_sftp}.py
- tests/build/, tests/scripts/, docs/features/content-staging/
