<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: AI agents working on CI/CD pipelines, and developers.
     Purpose: Orient anyone working on the pipeline - where the configs live, what the key files are,
     and any non-obvious decisions that aren't visible in the config itself.
     Do NOT duplicate what is already in the config files. -->

# CI/CD

## Config Location

- Main workflow files:
  - [`.github/workflows/build_site.yaml`](../.github/workflows/build_site.yaml)
  - [`.github/workflows/main.yaml`](../.github/workflows/main.yaml)
- Shared templates / includes: none beyond the reusable workflow pattern in `build_site.yaml`

## Key Files

| File                                                                                            | Purpose                                                                                    |
|-------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| [`.github/workflows/build_site.yaml`](../.github/workflows/build_site.yaml)                     | Reusable workflow called by host `comic_git` repos to build and deploy static sites        |
| [`.github/workflows/main.yaml`](../.github/workflows/main.yaml)                                 | Maintainer workflow for version updates, branches, tags, and GitHub releases               |
| [`requirements.txt`](../requirements.txt)                                                       | Core runtime Python dependencies installed during build workflow execution                 |
| [`requirements_migration.txt`](../requirements_migration.txt)                                   | Migration-only Python dependencies for local one-off conversion tooling                    |
| [`src/scripts/make_requirements_hooks_file.py`](../src/scripts/make_requirements_hooks_file.py) | Generates optional hook dependency requirements during the build workflow                  |
| `requirements_hooks.txt`                                                                        | Generated file used only when theme hook dependencies are needed during workflow execution |

## Non-Obvious Decisions

- `build_site.yaml` is part of the product surface, not just internal CI. Host repos call it remotely via `uses: comic-git/comic_git_engine/.github/workflows/build_site.yaml@...`, so changes to that workflow affect end-user builds directly.
- Artifact paths must remain symmetric across jobs. The build uploads the contents of the resolved `OUTPUT_DIR`, so each deployment job must download the named artifact into that same directory before passing it to the hosting action.
- GitHub's artifact upload excludes files and directories whose names begin with `.` by default. GitHub Pages and Neocities retain that behavior. For SFTP, the build script filters hidden paths in its output and the artifact uploader preserves that directory as produced; see below. Underscore-prefixed generated files such as `_thumbnail.jpg` are ordinary files and are included.
- Runtime dependency changes are CI/CD-sensitive because every end-user build installs them. Treat dependency additions as product-impacting changes, not just local tooling changes.
- Migration-only dependencies belong in `requirements_migration.txt`, not `requirements.txt`, unless they become required for normal site builds.
- The build checks out the engine directly into `comic_git_engine/` using the configured version, with TOML taking precedence over legacy INI and `1.1` as the fallback. Caller submodules are not initialized, so a committed engine submodule does not override that version or require remote-tracking branches during CI.
- Host repos make two independent version choices: the reusable workflow revision in `uses: .../build_site.yaml@...` and the engine revision in their comic configuration. Changing one does not change the other.
- `v1` is frozen at the 1.0 reusable-workflow contract. Major tags are managed manually and are never created, moved, or deleted by `main.yaml`.

## SFTP Deployment Contract

`DEPLOY_TARGET: sftp` consumes the same build as the other targets. The deployment
job installs `lftp` on its Ubuntu runner; local builds and the engine's Python
dependencies do not change. The build's output handling owns hidden-file
filtering, destination/exclusion validation, and deployment-file generation in
[`src/build/output/sftp.py`](../src/build/output/sftp.py). SFTP requires an engine
revision supporting `--hidden-paths` and `--sftp-deploy-dir`. The workflow passes
those options explicitly, so older engines fail rather than silently ignoring
deployment preparation. Other targets do not receive these options.

The build writes a separate `sftp-deployment` artifact under the runner's temporary
directory. It contains `deploy.lftp` (the destination and mirror command),
`connection.json` (host and port), and `deploy.py` (a self-contained copy of the
standard-library-only runner). It contains no credentials and is never part of
the public site artifact. Deployment files must be outside both the site output
and source directories. The `lftp` script uses the site's local working directory,
so the artifacts remain usable after downloading them to a different location.

The deployment job only downloads the two artifacts, installs `lftp`, and runs
`deploy.py --output-dir ...` with the authentication secrets. The runner prepares
temporary SSH credentials, opens the connection, and executes the generated
script. It does not recalculate cleanup, exclusions, destination, or site layout.
This keeps all deployment behavior in importable Python code while keeping
credentials out of builds and artifacts. The `index.html` check is performed
when preparing the artifact and again immediately before transferring it.

Password authentication is the default setup to describe to creators. The caller
passes `SFTP_USERNAME`, `SFTP_PASSWORD`, and `SFTP_KNOWN_HOSTS` as GitHub secrets.
Alternatively, pass an unencrypted OpenSSH key as `SFTP_PRIVATE_KEY` instead of
the password. Supplying both or neither fails. Private keys and known-host data
are written outside the published tree and removed when the transfer completes
or fails. Passwords are passed through the process environment, not generated
command text.

The caller supplies `SFTP_HOST` (DNS name or IPv4 address), `SFTP_PORT` (22 by
default), and `SFTP_REMOTE_DIR`. The remote directory must already exist. Absolute
paths and paths relative to the SFTP login directory are supported; root, common
home/system directories, and traversal paths are rejected. These checks cannot
prove that a server-side alias or symlink points to the intended website, so the
operator must confirm the actual web directory before testing.

`SFTP_CLEAN` defaults to `true`: comic_git owns the entire destination directory.
Files absent from the artifact, including hidden files, are removed. Set it to
`false` to retain old remote files. `SFTP_EXCLUDE_PATHS` accepts newline-separated,
exact relative file/directory paths that are left untouched by both upload and
cleanup. A directory entry protects its descendants; entries are not globs.
For example, `.well-known` can preserve server-managed certificate challenges.

`your_content/site_root/` is still copied into the generated root by the engine.
For SFTP, the workflow passes `SFTP_HIDDEN_PATHS` to the build's `--hidden-paths`
option. After copying assets and running postprocess hooks, the output handler
filters dotfiles and hidden directories in place, without creating another copy
of the site. The option explicitly includes exact output-relative paths,
one per line, such as `.htaccess` or `.well-known/security.txt`. A directory entry
includes its entire subtree, including nested hidden files. Missing entries fail
the build to catch configuration mistakes. Do not list `your_content/site_root/`
as a prefix: these paths refer to the final website root. Normal files need no
inclusion entry. SFTP itself does not require any dotfiles; `.htaccess` is an
Apache configuration file, while `.well-known` is commonly used for verification
and other web standards. A hidden path omitted from the artifact is **not**
protected against cleanup: add it to the exclusion list if the server owns it.

An empty `--hidden-paths` value removes all hidden paths. Omitting the option
preserves existing local-build behavior. Filtering requires a separate output
directory and rejects in-place/source-tree output before build cleanup begins;
it never filters the source repository. Symlinks in filtered output are rejected.
The default `build/` output is supported; legacy `OUTPUT_DIR: ''` is not supported
for SFTP builds. The artifact uploader directly uploads `OUTPUT_DIR` with hidden
files enabled only for SFTP, after the build has applied the allowlist.

The client verifies the server against the supplied `SFTP_KNOWN_HOSTS`; it does
not automatically trust `ssh-keyscan` output or accept unknown host keys. This
server identity check is separate from the creator's choice of password versus
private-key authentication. Nonstandard ports require `[hostname]:port` entries.
Obtain the entry and verify its fingerprint through the hosting provider or an
independently trusted connection before storing it.

The transfer sends all included files each time, because artifact timestamps
cannot reliably identify changed content. This includes same-size edits and
rollbacks. Transfers are in-place, not atomic: a failed run may leave a partially
updated site, and a subsequent successful run restores the mirror. Deployment
runs remain serialized by the existing workflow concurrency group. The client
uses bounded retries and a 30-minute job timeout. Builds without `index.html`
are rejected before transfer to prevent an empty artifact from clearing a site.

### DreamHost validation and documentation handoff

Before release, validate both authentication methods against a dedicated test
website and port the creator setup instructions to `comic_git_docs`. That guide
must lead with passwords and cover these steps:

1. Find the website's SFTP hostname, website user, and actual web directory in
   DreamHost. The usual path is `/home/username/example.com`, not `/home/username`.
2. Set the comic's domain and subdirectory to its public URL; the SFTP directory
   is a filesystem location, not a public URL. Do not leave the GitHub Pages URL
   inferred from the repository.
3. Select reusable-workflow and engine revisions containing SFTP support, set
   `DEPLOY_TARGET`, host, port, and directory in the caller YAML, and explicitly
   map the three password-mode secrets listed above. The `sftp` GitHub environment
   may add deployment protection rules.
4. Explain default directory ownership/cleanup and the optional cleanup toggle,
   hidden-path inclusion list, and untouched-path exclusion list.
5. Document private-key authentication as an alternative, including registering
   the matching public key with the host. DreamHost's key setup documentation
   assumes a shell-enabled website user; the deployment itself only uses SFTP.
6. Test create/update/remove behavior, same-size edits, a failed login or host-key
   mismatch, preserved excluded files, `.htaccess` inclusion, and rerunning after
   a partial failure. No live DreamHost deployment is implied by local tests.

References: [DreamHost credentials](https://help.dreamhost.com/hc/en-us/articles/115000675027-FTP-overview-and-credentials),
[DreamHost website directories](https://help.dreamhost.com/hc/en-us/articles/214920778-Where-do-I-upload-my-files-once-connected-via-FTP),
[DreamHost key setup](https://help.dreamhost.com/hc/en-us/articles/216499537-How-to-configure-passwordless-login-in-Mac-OS-X-and-Linux),
and the [lftp manual](https://lftp.yar.ru/lftp-man.html).

## Version Source Of Truth

For `1.1`, the engine version source of truth is:

- [`src/build/site_builder.py`](../src/build/site_builder.py)
  - the `VERSION = "..."` constant
- [`.github/workflows/build_site.yaml`](../.github/workflows/build_site.yaml)
  - the `DEFAULT_ENGINE_VERSION = "..."` fallback used when host config omits an engine version

The maintainer release workflow in [`.github/workflows/main.yaml`](../.github/workflows/main.yaml) updates the `VERSION` constant and the reusable workflow fallback before it creates version branches, tags, and the GitHub release.

For a release such as `1.1.0`, the workflow manages these references:

| Reference | Stability | Purpose                                                                |
|-----------|-----------|------------------------------------------------------------------------|
| `latest`  | Moving    | Most recent engine release                                             |
| `1.1`     | Moving    | Engine selector that receives compatible 1.1 patch releases            |
| `v1.1`    | Moving    | Reusable-workflow selector that receives compatible 1.1 patch releases |
| `1.1.0`   | Immutable | Exact engine branch                                                    |
| `v1.1.0`  | Immutable | Exact reusable-workflow tag and GitHub Release tag                     |

The normal host defaults are workflow `@v1.1` and engine version `1.1`. A host that requires an exactly reproducible build must pin both selectors independently to `@v1.1.0` and `1.1.0`.

When checking release readiness, verify these checks together:

- `main.yaml` still edits `src/build/site_builder.py`
- `main.yaml` still updates `DEFAULT_ENGINE_VERSION` in `build_site.yaml` to the release major/minor value
- the requested release version matches the updated `VERSION` constant
- the created branches and tags match that same version

## Release Workflow Safety and Recovery

Dispatch `main.yaml` from `master` with a canonical numeric `X.Y.Z` version. Its validation phase rejects non-`master` dispatches, malformed versions, older active release runs, and versions whose exact branch or tag already exists. The mutation phase is serialized and also rejects a changed `master` commit before writing anything.

The repository and organization policies must allow the workflow's declared token permissions to take effect: `actions: read` for overlap detection and `contents: write` for the version commit, branches, tags, and draft release. Rules protecting `master` must also permit this workflow's GitHub Actions identity to push the version commit. If policy blocks either capability, keep the protection in place and adjust the release process deliberately; do not broaden permissions without reviewing the repository rules.

The workflow creates a draft GitHub Release. Review and publish that draft separately; creating refs does not publish the release announcement automatically.

Recovery depends on the last completed mutation:

- If validation failed or no version commit was pushed, fix the cause, review current `master`, and dispatch again.
- If the version commit reached `master` but neither exact reference exists, dispatching the same version again can reuse that commit.
- If the exact branch or exact tag exists, do not rerun the workflow for that version. Inspect the remote state and manually complete any missing moving/exact refs and draft release. Never move an exact ref.
- If only draft-release creation failed, create the draft manually from the existing exact tag.
- If a published release is bad, repoint moving aliases where appropriate and issue a new patch. Exact refs remain evidence of what was published.

The early overlap check makes the newer run fail instead of silently waiting behind an older manual release. The serialized mutation job and stale-`master` check are still the authoritative race protection.

See [Release reference policy](decisions/2026-09-04-release-reference-policy.md) for the stability guarantees behind these rules.

## Jobs Requiring Care

- [`.github/workflows/build_site.yaml`](../.github/workflows/build_site.yaml)
  - This is the end-user integration surface.
  - Changes here can break builds across many host repos at once.
- [`.github/workflows/main.yaml`](../.github/workflows/main.yaml)
  - This controls version bumps, release tags, and release artifacts for `comic_git_engine`.
  - Mistakes here can create confusing or incorrect release state.
- Dependency installation steps in `build_site.yaml`
  - These affect every automated end-user build.
  - Runtime dependency changes should be reviewed very carefully.
