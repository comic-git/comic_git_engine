# Webring JSON Endpoint

**Version / API version:** JSON format version `1`
**Used for:** Loading webring member data into templates so comics can render previous/next member links or a full member list
**Canonical docs:** No formal external API spec is bundled in this repo. The effective contract is defined by [`build_site.py`](../../scripts/build_site.py), the tests in [`test_build_site.py`](../../tests/test_build_site.py), and example JSON such as `your_content/webring.json` in host repos

## Authentication

None.

The engine reads a public JSON endpoint or a host-repo-relative JSON file. No tokens, headers, or session state are involved.

## How We Use It

The engine reads the endpoint configured in `[Webring] Endpoint` and expects a JSON document with:

- `version`
- `home`
- `members`
- optionally `label`

Current supported behavior:

- `version` must be `1`
- `home` is passed through to templates as `webring_home`
- `label` is passed through as `webring_label`
- `members` is used either to:
  - compute `webring_prev` and `webring_next`, or
  - populate `webring_members` when `Show all members = True`
- `Enable webring = True` requires `Endpoint` to be defined
- when `Show all members = False`, `Webring ID` must be defined and must exactly match one of the member IDs
- previous/next navigation wraps around from the ends of the member list
- `Exclude own comic from members` only affects `Show all members = True`

Required member fields are whatever the templates expect, but current tests assume:

- `id`
- `name`
- `url`
- `image`

## Environment Differences

There are two practical endpoint modes:

- absolute URL, such as `https://example.com/webring.json`
- root-relative path, such as `/your_content/webring.json`

If the endpoint starts with `/`, the engine resolves it relative to the computed comic URL. That makes local and hosted behavior depend on the current `comic_url` resolution.

Examples:

- hosted: `https://ryanvilbrandt.github.io/comic_git_dev/your_content/webring.json`
- local, via host repo preview: whatever `comic_url` resolves to for that local setup

## Local Development

For local development, the easiest path usually is:

- place a `webring.json` file in the host repo, often at `your_content/webring.json`
- set `[Webring] Endpoint = /your_content/webring.json`

For unit tests:

- mock `urlopen`
- mock `json.load`

Current test coverage for this integration lives in [`tests/test_build_site.py`](../../tests/test_build_site.py).

## Gotchas

- If `Show all members = False` and the configured `Webring ID` is missing from the JSON, the engine prints the received webring data to logs before raising an error
- Root-relative endpoints are resolved against the computed `comic_url`, so local preview and hosted behavior depend on correct comic URL resolution
- The engine does not validate the full schema beyond the fields it reads, so malformed or incomplete member objects may fail later in templates instead of during parsing

## Related Decisions

No dedicated decision doc yet. The main architectural context is captured in [`docs/architecture.md`](../architecture.md).
