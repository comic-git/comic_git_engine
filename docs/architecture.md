<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: AI agents and human developers.
     Purpose: Describe the system's structure, key components, and design rationale.
     This is the first doc an AI agent should read to understand what this system does and how it's organized.
     Do not duplicate content from model files or API specs - link to them instead. -->

# Architecture

## Overview

`comic_git_engine` is a Python-based static site build engine for `comic_git`. It is designed to be loaded from a user-facing `comic_git` repo, usually as a git submodule or symlinked engine, and it turns the host repo's file-based `your_content/` data into a complete static webcomic site intended for GitHub Pages deployment.

## Components

| Component                   | Location                                                                    | Responsibility                                                                                                                            |
|-----------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| Build entry point           | [`src/build/build_site.py`](../src/build/build_site.py)                     | Thin orchestration entry point. Handles env input setup, host-root discovery, hook boundaries, main/extra comic coordination, and RSS.    |
| Build pipeline modules      | [`src/build/`](../src/build/)                                               | Purpose-built modules for the build pipeline, including site config, page discovery, comic data assembly, rendering, output handling, and image/transcript helpers. |
| Shared utilities            | [`src/core/utils.py`](../src/core/utils.py)                                 | Cross-cutting helpers for root discovery, config parsing, path/url building, templating, social media data, and build checkpoints.        |
| RSS generation              | [`src/integrations/rss.py`](../src/integrations/rss.py)                     | Builds RSS feed jobs and serializes RSS XML for the main comic and Extra Comics.                                                          |
| Page and image models       | [`src/build/content/page_models.py`](../src/build/content/page_models.py)   | Structured page/image/archive models plus stable identity, anchor, and fallback helpers.                                                   |
| Shared build models         | [`src/core/models.py`](../src/core/models.py)                               | Small shared dataclasses used to pass per-comic build results between top-level steps.                                                     |
| Public metadata contract    | [`src/build/content/page_metadata.py`](../src/build/content/page_metadata.py), [`schemas/`](../schemas/) | Serializes resolved page/image data and ships its versioned JSON Schema. |
| Hooks and external data     | [`src/integrations/`](../src/integrations/)                                 | Theme hooks, RSS integration logic, and webring loading.                                                                                  |
| Built-in presentation layer | [`templates/`](../templates/), [`css/`](../css/), [`js/`](../js/)           | Default templates, CSS, and JavaScript shipped with the engine. These provide the default site behavior and appearance.                   |
| Host-repo content layer     | `your_content/` in the loading `comic_git` repo                             | User-controlled data source: comic config, page metadata, images, themes, transcripts, home page content, and Extra Comic content.        |
| Theme extension layer       | `your_content/themes/...` in the loading repo                               | Optional theme-level templates, CSS, images, and Python hook scripts that override or extend default engine behavior.                     |
| Reusable build workflow     | [`.github/workflows/build_site.yaml`](../.github/workflows/build_site.yaml) | Reusable GitHub Actions workflow intended to be called from host `comic_git` repos to build and deploy sites with shared engine behavior. |
| Release workflow            | [`.github/workflows/main.yaml`](../.github/workflows/main.yaml)             | Maintainer-only workflow for version bumps, tags, branches, and GitHub releases for `comic_git_engine` itself.                            |
| Test suite                  | [`tests/`](../tests/)                                                       | Unit tests for engine behavior, split by module so refactors can lock down behavior before moving code.                                   |

## Host Repo Data Model

The engine assumes it is running inside a host `comic_git` repo that contains a top-level `your_content/` directory. That directory is the primary input surface for creators.

Typical structure:

```text
your_content/
  comic_info.ini
  home page.txt|html
  site_root/
    .nojekyll
    favicon.ico
  webring.json
  images/
  comics/
    <page-name>/
      info.ini
      post.txt
      <comic image files>
      <transcript files>
  themes/
    <theme-name>/
      css/
      images/
      templates/
      scripts/
  <extra-comic>/
    comic_info.ini
    comics/
      <page-name>/
        info.ini
        post.txt
        <comic image files>
```

This structure is intentionally file-based and low-friction:

- creators edit `.ini`, `.txt`, and image files directly
- most configuration is designed to be understandable in a text editor on Windows
- adding or changing content is usually done by creating, renaming, moving, or deleting files and folders
- `your_content/site_root/` is part of the expected 1.1 host-repo layout, and should contain at minimum a `favicon.ico` and `.nojekyll` file.

## Data Flow

1. A host `comic_git` repo invokes the engine locally or through the reusable [`build_site.yaml`](../.github/workflows/build_site.yaml) workflow.
2. [`src/build/build_site.py`](../src/build/build_site.py) finds the project root, reads `your_content/comic_info.ini`, resolves the site URL, loads theme hooks, and orchestrates the build order for Extra Comics and the main comic.
3. [`src/build/site_builder.py`](../src/build/site_builder.py) coordinates the per-comic build pipeline using the lower-level modules.
4. [`src/build/content/page_sources.py`](../src/build/content/page_sources.py) parses legacy INI or TOML into source-only page/image models, preserving omitted versus explicitly blank values.
5. [`src/build/content/page_discovery.py`](../src/build/content/page_discovery.py) scans page folders, applies scheduling and source precedence, validates image paths, resolves fallbacks once, and constructs ordered `ComicPage`/`ComicImage` models.
6. [`src/build/content/comic_data.py`](../src/build/content/comic_data.py) enriches pages with navigation, post HTML, archive dates, and the structured hook boundary.
7. [`src/build/output/images.py`](../src/build/output/images.py) resolves page and image thumbnails according to archive mode, generation, explicit-asset, and overwrite policies.
8. [`src/build/content/page_metadata.py`](../src/build/content/page_metadata.py) writes resolved public metadata after thumbnail processing. Every build also deploys [`schemas/page_info_list.schema.json`](../schemas/page_info_list.schema.json).
9. [`src/build/output/rendering.py`](../src/build/output/rendering.py) projects narrow template contexts and renders built-in or theme templates.
10. [`src/integrations/rss.py`](../src/integrations/rss.py) builds page-level RSS items from structured pages for the main comic and Extra Comics.
11. [`src/build/output/site_output.py`](../src/build/output/site_output.py) handles cleanup, staging into the configured output directory, and copying any host-managed root files from `your_content/site_root/` into the built site root.
12. The host repo then publishes that output, typically to GitHub Pages and optionally to Neocities.

## Key Dependencies

| Dependency              | Purpose                             | Notes                                                                                                                                      |
|-------------------------|-------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| GitHub Actions          | Primary automated build environment | The engine is designed to be called remotely from host repos via `uses: comic-git/comic_git_engine/.github/workflows/build_site.yaml@...`. |
| GitHub Pages            | Primary publishing target           | Static-site-only architecture is shaped around GitHub Pages constraints.                                                                   |
| Neocities               | Optional publishing target          | Supported as an alternate deployment target via the reusable workflow.                                                                     |
| Jinja2                  | HTML template rendering             | Used for both built-in templates and host-repo theme overrides.                                                                            |
| markdown2               | Markdown to HTML conversion         | Used for post text, markdown pages, and transcript-related content.                                                                        |
| Pillow                  | Image processing                    | Used for thumbnails and image format handling.                                                                                             |
| pytz                    | Timezone-aware scheduling           | Used when deciding which scheduled pages are publishable.                                                                                  |
| Theme hook dependencies | Optional extension point            | Theme-specific Python dependencies are not part of the normal runtime install and are only added when needed.                              |

## API / Data Model

- API spec: none; this repo does not expose a network API
- Internal page/image models: [`src/build/content/page_models.py`](../src/build/content/page_models.py)
- Public page metadata schema: [`schemas/page_info_list.schema.json`](../schemas/page_info_list.schema.json)
- Primary host-repo config/data inputs:
  - `your_content/comic_info.ini`
  - `your_content/comic_info.toml`
  - `your_content/comics/*/info.ini|info.toml`
  - `your_content/<extra-comic>/comic_info.ini`

## Features

Feature intent and product rules are indexed in [`docs/features/`](features/README.md).

## Design Decisions

- This repo is intentionally a static-site build engine, not a long-running service. That constraint comes both from the product goal and from GitHub Pages as the default publishing target.
- The reusable [`build_site.yaml`](../.github/workflows/build_site.yaml) workflow is a core part of the architecture. Host `comic_git` repos are expected to call this workflow remotely so engine behavior can be centralized and updated for many users at once.
- [`main.yaml`](../.github/workflows/main.yaml) is a maintainer workflow for releasing `comic_git_engine` itself and is not part of the end-user integration surface.
- Host `comic_git` repos should be thought of primarily as user data stores plus a small amount of scaffolding. The engine repo is where the main build logic, defaults, and shared behavior live.
- The user-content model prioritizes minimal technical intimidation. File formats, defaults, and content layout are designed so non-technical creators can work mostly through folders, `.ini` files, `.txt` files, and image assets.
- Runtime dependencies should stay minimal because they are installed during GitHub Actions runs for end-user sites. Developer-only tools should not become required engine runtime dependencies.
