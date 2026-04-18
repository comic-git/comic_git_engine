# Webring JSON Endpoint

**Version / API version:** JSON format version `1`
**Used for:** Loading webring member data into templates so comics can render previous/next member links or a full member list
**Canonical docs:** No formal external API spec is bundled in this repo. The effective contract is defined by [`build_site.py`](../../scripts/build_site.py), the tests in [`test_build_site.py`](../../tests/test_build_site.py), and example JSON such as `your_content/webring.json` in host repos

## Authentication

None.

The engine reads either a public JSON endpoint or an explicit local-development file. No tokens, headers, or session state are involved.

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
- `Enable webring = True` also requires `Webring ID` to be defined
- `Webring ID` must exactly match one of the member IDs for previous/next navigation
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
- explicit local mode via `local`

If the endpoint is `local`, the engine reads `your_content/webring.json` directly from the host repo root. This mode exists only to make local development easier.

Examples:

- hosted/shared: `https://webring.example.com/webring.json`
- local development: `Endpoint = local`

## Local Development

For local development, the easiest path usually is:

- place a `webring.json` file in the host repo, often at `your_content/webring.json`
- set `[Webring] Endpoint = local`
- keep the `url` and `image` values inside the JSON as absolute URLs

For unit tests:

- mock `urlopen`
- mock `open` for local-mode reads
- mock `json.load`

Current test coverage for this integration lives in [`tests/test_build_site.py`](../../tests/test_build_site.py).

## Gotchas

- If `Show all members = False` and the configured `Webring ID` is missing from the JSON, the engine prints the received webring data to logs before raising an error
- `Endpoint = local` reads `your_content/webring.json` from the host repo root; it does not fetch that file over HTTP
- The engine does not validate the full schema beyond the fields it reads, so malformed or incomplete member objects may fail later in templates instead of during parsing

## Related Decisions

No dedicated decision doc yet. The main architectural context is captured in [`docs/architecture.md`](../architecture.md).
