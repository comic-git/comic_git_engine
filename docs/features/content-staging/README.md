<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: Maintainers. Purpose: Record publication rules that preserve patch compatibility. -->

# Selective content staging

Selective copying is opt-in for 1.1.1. Existing builds keep wholesale content
copying and the legacy destructive deletion flag. Native local SFTP opts in.

The main config owns site-wide `[Build] Selective copy` / `[build] selective_copy`.
`--selective-copy` and `--no-selective-copy` override it for one invocation. A
separate output directory is required. In selective mode the deletion flag never
deletes scheduled source folders. `--publish-all-comics` includes future pages.

Discovery's page models govern HTML, JSON, navigation, RSS, and copied page folders. Missing
metadata files or required values skip a folder with a diagnostic; malformed
documents and invalid supplied values fail. Valid text-only pages remain valid.
Every selected page folder is copied wholesale. Files directly under managed
`comics/` roots are always omitted. The same rules apply to configured Extra
Comics. Auxiliary content outside all managed roots retains its existing paths.
Unconfigured directories are not inferred to be Extra Comics.

The main configuration owns this policy for all comics; Extra Comic settings do
not independently select a copying mode. Normal scheduling applies in selective
mode even without the legacy deletion flag. A later rebuild after rescheduling
removes stale generated output while retaining source folders and cached thumbnails.

Thumbnail generation deliberately writes source files, respecting existing reuse
and overwrite settings, before copying. This preserves a cache users can commit.
It is not an immutable-source mode, and hooks can still write arbitrary files.
Selected INI/TOML and supporting text files remain public output.
The `!` convention filters generated JSON only; it does not sanitize copied
source files or turn source notes into private data.

## Hidden files

Selective mode excludes dotfiles and dot-directories by default. Main-config
`[Build] Include hidden files` / `[build] include_hidden_files = true` includes
them. Underscore-prefixed assets are ordinary files. This setting does not change
Windows hidden attributes, preview HTTP restrictions, scheduling/metadata validity,
or loose-file omission.

An explicit `--hidden-paths` overrides configured `[Build] Hidden paths` /
`[build] hidden_paths`; either exact-path allowlist overrides include-all. Empty
means exclude all hidden output. SFTP preparation defaults to an empty allowlist
and local SFTP explicitly passes `SFTP_HIDDEN_PATHS`. Paths refer to final output:
`.htaccess` permits the root copy from site_root, not its separate duplicate
under `your_content/site_root/`. Missing allowlisted output fails.

When an allowlist applies, filtering runs after asset copying, site_root copying,
and postprocess hooks; effective include-all retains hidden output. Hidden page
directories need include-all or an allowlist covering both their complete asset
directory (`your_content/comics/.page`) and generated HTML directory
(`comic/.page`). Hidden auto-discovered images are omitted when excluded; explicit
image/thumbnail references to excluded paths fail instead of producing broken
links. Input files may still be read even when omitted from public output.

## Boundaries

Reject in-place/overlapping output and link aliases in encountered selective
content. Validate selected identities before source thumbnail writes and copying;
hooks may change metadata but cannot substitute arbitrary source folders. Generic
copying prunes managed comics roots so it cannot restore scheduled pages. No
automatic reference discovery, source metadata sanitization, or new transfer
policy is implied. See the [decision](../../decisions/2026-11-07-opt-in-selective-content-staging.md).

## Verification

Unit tests cover policy resolution and managed-root pruning. Real-CLI engine
tests cover legacy overrides, invalid inputs, hidden pages, source caches, and
hook identity boundaries. The separate e2e repo's
`tests/test_selective_staging.py` validates fresh output against its deployed
schema and checks agreement across metadata, HTML/navigation, combined RSS, and
assets for main and nested Extra Comics. See [testing](../../testing.md) for commands.
