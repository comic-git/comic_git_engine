<!-- ai-agent-toolkit:managed version="1.0.0" -->

# Webring

| Field      | Value    |
|------------|----------|
| **Status** | `active` |

## Summary

This feature lets a comic_git site render a webring on its pages using member data loaded from a JSON endpoint.

It is a user-facing site feature built on top of an external JSON contract, with the engine responsible for turning that data into template-ready previous/next links or full member lists.

## Current State & Roadmap

The current webring model is endpoint-driven and opt-in:

- webring support is disabled unless enabled in `comic_info.ini`
- the site reads a JSON endpoint or host-repo-relative JSON file
- the webring can render as previous/next navigation or as a full member list
- the same external data source can be reused by multiple sites in the same ring

Important current behavior:

- the webring is configured per site through the `[Webring]` section
- previous/next behavior depends on the site's configured member ID within the shared member list
- local development can use a root-relative endpoint such as `/your_content/webring.json`
- the feature depends on external or externally-authored JSON data, so endpoint correctness is part of the effective product contract

This feature is stable in concept. The main maintenance risk is not internal complexity so much as the fact that generated site behavior depends on data outside the engine.

## Product Rules

- Webring support should remain optional and easy to disable entirely.
- A shared JSON endpoint should remain the main coordination mechanism between participating sites.
- The feature should support both minimal previous/next navigation and a full-member-list presentation.
- Local development should remain easy by allowing host-repo-relative JSON files.
- Refactors in this area should be reviewed carefully because template behavior depends on the external data contract and on URL resolution.

## Supporting Documents

| Document | Contents |
|----------|----------|
| [../../integration/webring.md](../../integration/webring.md) | The effective JSON endpoint contract and local-development behavior |
