# Webring JSON Endpoint

**Version / API version:** JSON format version `1`
**Used for:** Loading webring member data into templates so comics can render previous/next member links or a full member list
**Canonical docs:** No formal external API spec is bundled in this repo. The effective contract is defined by [`build_site.py`](../../src/build/build_site.py), the integration tests in [`tests/integrations/test_webring.py`](../../tests/integrations/test_webring.py), and example JSON such as `your_content/webring.json` in host repos

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

Current test coverage for this integration lives in [`tests/integrations/test_webring.py`](../../tests/integrations/test_webring.py).

## Gotchas

- Missing own IDs in previous/next mode fail validation; external payloads are not dumped into logs.
- `Endpoint = local` reads `your_content/webring.json` from the host repo root; it does not fetch that file over HTTP
- The loader validates member structure, unique IDs, and absolute HTTP(S) links before rendering. Optional names/images default to empty strings.
- Owner configuration selects `Text mode` / TOML `text_mode` (`text`, `markdown`, `unsafe_html`) and `On error` / `on_error` (`abort`, `omit`). Defaults are `text` and `abort`. See the [security decision](../decisions/2026-10-21-external-data-and-preview-security.md) for rationale and template boundaries.
- Responses are limited to 1 MiB. HTTP requests use a 10-second socket timeout and a 20-second deadline checked between body reads (an active read may last until its socket timeout), with at most two attempts for transient failures. Invalid JSON/schema and permanent HTTP errors are not retried. No cache is persisted.

## Related Decisions

No dedicated decision doc yet. The main architectural context is captured in [`docs/architecture.md`](../architecture.md).
