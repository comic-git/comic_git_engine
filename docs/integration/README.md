<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: AI agents and developers working with external services.
     Purpose: One file per external dependency — captures integration-specific knowledge
     that isn't in (or can't be retrieved from) the dependency's own documentation. -->

# External Integrations

This folder documents external APIs and services this repo depends on. Each file covers one dependency.

## When to add a file here

Create an integration doc when the external dependency has any of:
- **Non-obvious integration behavior** — auth patterns, pagination quirks, rate limits, error handling that differs from the docs
- **Repo-specific usage** — which endpoints or operations this repo uses, and why
- **Inaccessible canonical docs** — the official API spec requires auth to view, is poorly documented, or only exists in internal tooling
- **Environment differences** — test vs. production API behavior, sandbox gotchas
- **Local development notes** — how to mock or stub the dependency for local work

Do not duplicate the dependency's own documentation. Capture what the docs don't tell you, or can't tell an AI that can't access them.

## For AI agents

Before writing any code that touches an external service, check this folder for an existing integration doc. It may contain auth patterns, gotchas, or constraints that are not visible from the code alone.

## Structure

```
docs/integration/
  README.md               # This file
  _template.md            # Copy this when adding a new integration
  <dependency-name>.md    # One file per external dependency
```

Use kebab-case filenames matching the dependency name (e.g., `stripe.md`, `google-maps.md`, `internal-auth-service.md`).
