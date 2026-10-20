# SFTP directory ownership and publication

| Field | Value |
|---|---|
| Date | 2026-10-18 |
| Status | `active` |

## Context

Creators need a generic SFTP deployment target, with DreamHost as the initial test bed,
without having to learn SSH key management or manually remove obsolete pages.
The hosting directory may also contain server-managed files. Artifact upload
normally excludes dotfiles even when the engine copied them from `site_root`.

## Decision

- Document passwords as the normal authentication method and support SSH private
  keys as an alternative. Verify the server's host key in either mode.
- Treat the destination website directory as comic_git's property. Cleanup is on
  by default and can be disabled. Explicit excluded paths belong to the server
  and are neither overwritten nor deleted.
- Apply the explicit hidden-path allowlist in the build script's output handling,
  after asset copying and postprocess hooks. Upload the resulting directory
  directly, without a second staging copy. Preserve existing local-build and
  other deployment-target defaults when this policy is not requested.
- Have the build validate deployment settings and generate the `lftp` script and
  standalone runner in a separate, non-public artifact. Keep this logic in a
  standard-library-only Python module so it can be unit-tested without extracting
  code from YAML. The workflow downloads artifacts, installs the client, and
  invokes the runner.
- Supply credentials only at deployment time. The runner owns their temporary
  files and cleanup; the build never serializes them into either artifact.
- Pass `--hidden-paths` and `--sftp-deploy-dir` explicitly, requiring an engine
  that supports preparation; older engines fail rather than ignoring the policy.
- Require separate generated output for filtering, protecting source files from
  deletion in legacy in-place builds.
- Use SFTP alone, without requiring remote shell commands or rsync. Transfer all
  included files so artifact timestamp changes cannot hide same-size updates.

## Consequences

Removed comics disappear automatically. A wrong destination can remove unrelated
files; validation rejects obvious unsafe paths but cannot establish ownership.
An omitted hidden file may be removed during cleanup unless explicitly excluded.
The initial implementation favors predictable updates over incremental transfer
performance and does not promise atomic publication or automatic rollback.

## Files Affected

- `.github/workflows/build_site.yaml`
- `src/build/build_site.py`
- `src/build/output/site_output.py`
- `src/build/output/sftp.py`
- `tests/build/test_build_site.py`
- `tests/build/output/test_site_output.py`
- `tests/build/output/test_sftp.py`
- `tests/scripts/test_sftp_workflow.py`
- `docs/cicd.md`
- `docs/features/sftp/README.md`
