<!-- ai-agent-toolkit:managed version="1.0.0" -->

# Social media previews

| Field      | Value    |
|------------|----------|
| **Status** | `active` |

## Summary

This feature controls the metadata comic_git emits for link previews on platforms such as Discord, Facebook, and other Open Graph consumers.

It combines built-in defaults with optional user-owned override files so sites can get useful preview metadata without requiring every creator to hand-author it from scratch.

## Current State & Roadmap

The current social-preview model is default-first with selective override:

- comic_git emits Open Graph-style metadata automatically
- a default preview image is expected at `your_content/images/preview_image.png`
- page-type-specific defaults exist for site pages and comic pages
- metadata can be customized through `social_media.json`
- an individual comic page can also provide its own `social_media.json`

Important current behavior:

- preview metadata is generated as part of normal page rendering
- comic pages default to article-like metadata, including page text and thumbnail-based image fields
- fallback metadata still exists when no custom JSON file is provided
- Extra Comics can have different social-media metadata because data is scoped per comic folder

This feature is stable in purpose, but changes here are externally visible and can affect how pages appear when shared across third-party platforms.

## Product Rules

- Sites should get reasonable social preview metadata by default without requiring deep customization.
- Override points should remain available for creators who need custom per-site or per-page preview behavior.
- Default preview behavior should stay consistent across the main comic and Extra Comics unless explicitly overridden.
- Refactors in this area should be reviewed carefully because preview metadata is part of the public output contract and is consumed by third-party platforms outside the engine's control.

## Supporting Documents

| Document | Contents |
|----------|----------|
| [../../decisions/2026-04-12-built-output-and-extension-model.md](../../decisions/2026-04-12-built-output-and-extension-model.md) | Why generated metadata is treated as intentional static output rather than incidental implementation detail |
| [../themes-and-presentation-overrides/](../themes-and-presentation-overrides/) | Theme and template customization paths that often interact with preview metadata presentation |
