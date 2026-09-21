<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: Maintainers updating the Decap CMS browser runtime bundled with the engine.
     Purpose: Provide the deliberate, reproducible procedure for replacing a vendored runtime. -->

# Updating the Vendored Decap Runtime

Use this procedure only when a reviewed Decap change or release must replace
the runtime shipped with `comic_git_engine`. It is not the normal local-Decap
development workflow; use `dev_server.py --decap-cms-repo` for that.

The engine commit is the immutable pin for the browser code creators receive.
Never build from a moving branch, overwrite a runtime directory, or load a
runtime from a CDN as part of this process. Read the active
[vendoring decision](../../decisions/2026-09-20-vendored-decap-runtime.md)
before starting.

## Prerequisites

- A reviewed commit in `comic-git/decap-cms`, or a reviewed upstream release
  commit that contains every required fix.
- Clean working trees in `decap-cms`, `comic_git_engine`, and `e2e_tests`.
- Node.js with Corepack available, plus the Python environments used by the
  engine and e2e tests.
- A local checkout layout where `decap-cms`, `comic_git_engine`, and
  `e2e_tests` are sibling repositories. Adjust the paths below only if the
  layout differs.

## Build and Stage the Runtime

Run the following from the `decap-cms` checkout. Replace `<reviewed-ref>` with
the exact reviewed branch, tag, or commit. Confirm the resulting full commit
SHA in review before continuing.

```powershell
git switch <reviewed-ref>
git rev-parse HEAD
corepack pnpm install --frozen-lockfile
corepack pnpm --filter decap-cms run build
```

Create a new engine runtime directory from the package version and the first
12 characters of that full commit SHA. The selected assets are the entry
script, its license notice, lazy-loaded `*.decap-cms.js` chunks, and WASM
files. Do not include `cms.js`, source maps, or any other build artifact.

```powershell
$source = Resolve-Path .\packages\decap-cms\dist
$version = node -p "require('./packages/decap-cms/package.json').version"
$commit = (git rev-parse HEAD).Trim()
$runtimeName = "decap-cms-$version-comic-git-$($commit.Substring(0, 12))"
$runtime = Join-Path ..\comic_git_engine "vendor\decap-cms\$runtimeName"

if (Test-Path $runtime) { throw "Refusing to overwrite existing runtime: $runtime" }
New-Item -ItemType Directory -Path $runtime | Out-Null
Copy-Item "$source\decap-cms.js" $runtime
Copy-Item "$source\decap-cms.js.LICENSE.txt" $runtime
Get-ChildItem $source -File |
    Where-Object { $_.Name -like '*.decap-cms.js' -or $_.Extension -eq '.wasm' } |
    Copy-Item -Destination $runtime
```

Generate the required ASCII, LF-terminated manifest. It records the exact
source and hashes every copied runtime file; it intentionally does not list
itself. Run this from the `decap-cms` checkout after the copy step.

```powershell
@'
from hashlib import sha256
import json
from pathlib import Path
import sys

runtime = Path(sys.argv[1])
version = sys.argv[2]
commit = sys.argv[3]
files = [
    {"name": path.name, "sha256": sha256(path.read_bytes()).hexdigest()}
    for path in sorted(runtime.iterdir())
    if path.is_file() and path.name != "comic_git_engine_manifest.json"
]
manifest = {
    "asset_kind": "comic_git_engine_decap_runtime",
    "decap_version": version,
    "fork_repository": "https://github.com/comic-git/decap-cms",
    "fork_commit": commit,
    "upstream_repository": "https://github.com/decaporg/decap-cms",
    "build_command": "corepack pnpm --filter decap-cms run build",
    "files": files,
}
(runtime / "comic_git_engine_manifest.json").write_text(
    json.dumps(manifest, indent=2) + "\n", encoding="ascii", newline="\n"
)
'@ | python - $runtime $version $commit
```

For an upstream-only release, change the manifest source fields to accurately
name the reviewed source. If its directory name should no longer identify the
comic-git fork, change the engine naming constants and tests together rather
than disguising the source.

## Wire the Engine and Refresh Output

In `comic_git_engine/src/build/output/cms.py`, update
`DECAP_CMS_VERSION` and `DECAP_CMS_FORK_COMMIT`. The derived directory and
script-path constants must resolve to the new runtime directory. Keep
`vendor/decap-cms/** -text` in `.gitattributes`; the runtime's byte hashes and
third-party license notice must not be line-ending-normalized. Keep the narrow
license `-diff` rule so `git diff --check` does not reject whitespace retained
verbatim from the upstream notice.

Then refresh the committed CMS output from the `e2e_tests` checkout:

```powershell
python scripts\run_e2e.py refresh-build --case cms-pages
python scripts\run_e2e.py check-build --case cms-pages
```

Do not hand-copy the engine runtime into `golden_builds`. Refreshing through
the harness proves that engine output contains exactly the assets the browser
will load.

## Validate and Review

Run these focused checks before reviewing the full change:

```powershell
# From comic_git_engine
.\venv\Scripts\python.exe -m unittest tests.build.output.test_cms tests.build.output.test_site_output tests.scripts.test_entrypoints

# From e2e_tests
venv\Scripts\python.exe -m pytest tests\generated_site_contracts\test_cms.py tests\test_cms_browser_harness.py
venv\Scripts\python.exe -m pytest -m browser tests\browser\test_cms_browser.py
```

The runtime-manifest test verifies every runtime hash. The generated-site
contract verifies the deployed script path and manifest. Browser tests exercise
the same vendored runtime by default; inspect any expected failures to confirm
they still represent intentionally deferred Decap behavior.

Finally, review all the following:

1. The manifest's source URL, full commit SHA, package version, build command,
   and hashes match the reviewed Decap checkout.
2. The runtime contains only the required entry script, chunks, WASM files,
   license notice, and manifest. It contains no source maps or `cms.js`.
3. The engine and CMS golden output use the identical versioned directory.
4. `git diff --check` passes in both repositories without altering the
   third-party license notice.
5. A local CMS proof uses the normal vendored runtime, not
   `--decap-cms-repo`, and covers the Decap behavior being adopted.

After the replacement is accepted, remove an older engine runtime directory
only when it is no longer useful for review or rollback comparison. Never
rename the new directory to reuse the old versioned URL.
