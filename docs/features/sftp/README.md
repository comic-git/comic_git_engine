<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: Developers maintaining SFTP deployment.
     Purpose: Record SFTP publication rules and failure boundaries that are not obvious from workflow code. -->

# SFTP deployment

| Field      | Value    |
|------------|----------|
| **Status** | `active` |

## Summary

SFTP publishes a built comic_git site to an existing website directory on a
conventional web host. Creators set the comic's public domain and subdirectory
separately from the server's filesystem path.

## Product rules

- Passwords are the normal setup to explain to creators. An unencrypted OpenSSH
  private key is also supported. Exactly one authentication method must be
  supplied, and both require a verified server host key. The transfer receives
  credentials after the build. Site output and deployment artifacts contain no
  credentials supplied through the SFTP settings.
- comic_git owns the selected website directory. Cleanup is on by default, so
  obsolete pages and other files disappear. `SFTP_CLEAN: false` retains them.
  Exact paths in `SFTP_EXCLUDE_PATHS` belong to the server and are neither
  uploaded nor deleted; use this for server-managed paths such as `.well-known`.
- Files from `your_content/site_root/` reach the generated website root. Hidden
  output is published only when its final output-relative path is explicitly
  listed in `SFTP_HIDDEN_PATHS`. The build applies that allowlist after asset
  copying and postprocess hooks. A listed path that is missing fails the build.
  Hidden paths not published can be deleted by cleanup, so exclude any that the
  server must retain. SFTP itself requires no dotfiles; `.htaccess` is an Apache
  configuration file, not an SFTP requirement.
- The destination must already exist. Validation rejects obvious unsafe paths,
  but cannot prove that a server-side alias or symlink points to the intended
  website. The operator must verify the actual web directory before deploying.
  A build without `index.html` cannot transfer, limiting the risk of clearing a
  site with an empty artifact.
- Each deployment sends all included files. Artifact timestamps are unreliable
  for detecting same-size edits and rollbacks. Publication is not atomic: a
  failed transfer can leave a partially updated site, and a successful rerun
  restores the mirror.

## Build and workflow boundary

In GitHub Actions, the build owns publication policy and prepares a separate, credential-free
deployment bundle. The deploy job only transfers the prepared site with the
credentials supplied at that point. This makes the same policy testable without a
live server. SFTP requires a separate output directory so filtering cannot remove
source files; legacy in-place output is unsupported. GitHub Pages and Neocities
retain their existing hidden-file artifact behavior.

The local command enables [selective staging](../content-staging/), building
from the actual host checkout into temporary output. Future source folders remain
intact and hooks can read host-owned inputs; thumbnail generation still creates
or updates the committable source cache. Existing previews remain separate.
Its optional Python SFTP dependencies support native Windows environments
and stay out of regular builds and the GitHub artifact runner. Run the engine's
loopback tests with `requirements_sftp.txt` installed to exercise both
authentication methods and host-key verification.

Hosted SFTP builds keep legacy content copying unless the main config opts into
selective staging. The native local command always enables it. Both use the
explicit SFTP hidden-path allowlist, which takes precedence over configured
include-all; local transfer does not prepare or execute the Actions `lftp` bundle.
The local command suppresses build-subprocess bytecode writes so importing theme
hooks does not add Python cache files to creator content. `--publish-all-comics`
on that command explicitly uploads future pages too.

## Supporting documents

- [SFTP directory ownership decision](../../decisions/2026-10-18-sftp-directory-ownership.md)
  records why cleanup, exclusions, and output filtering work this way.
- [CI/CD](../../cicd.md) describes the shared workflow and version selectors.
- Creator setup and hosting instructions belong in `comic_git_docs`.
