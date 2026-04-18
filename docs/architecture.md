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
| Data models                 | [`src/core/models.py`](../src/core/models.py)                               | Small shared dataclasses used to pass build results between steps.                                                                        |
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

## Data Flow

1. A host `comic_git` repo invokes the engine locally or through the reusable [`build_site.yaml`](../.github/workflows/build_site.yaml) workflow.
2. [`src/build/build_site.py`](../src/build/build_site.py) finds the project root, reads `your_content/comic_info.ini`, resolves the site URL, loads theme hooks, and orchestrates the build order for Extra Comics and the main comic.
3. [`src/build/site_builder.py`](../src/build/site_builder.py) coordinates the per-comic build pipeline using the lower-level modules.
4. [`src/build/page_discovery.py`](../src/build/page_discovery.py) scans `your_content/comics/` and any configured Extra Comics for page folders, scheduling state, and page metadata, then writes `page_info_list.json`.
5. [`src/build/comic_data.py`](../src/build/comic_data.py) normalizes page metadata into full comic data dictionaries, including post text, transcripts, navigation IDs, derived titles, and other template variables.
6. [`src/build/images.py`](../src/build/images.py) optionally creates thumbnails and other image derivatives.
7. [`src/build/rendering.py`](../src/build/rendering.py) renders Jinja templates from the built-in template set and any theme overrides into HTML output.
8. [`src/integrations/rss.py`](../src/integrations/rss.py) builds any enabled RSS feeds for the main comic and Extra Comics.
9. [`src/build/output/site_output.py`](../src/build/output/site_output.py) handles cleanup and staging into the configured output directory, which now defaults to `build/`.
10. The host repo then publishes that output, typically to GitHub Pages and optionally to Neocities.

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
- Data models: [`src/core/models.py`](../src/core/models.py)
- Primary host-repo config/data inputs:
  - `your_content/comic_info.ini`
  - `your_content/comics/*/info.ini`
  - `your_content/<extra-comic>/comic_info.ini`

## Features

No feature-specific folders have been created yet in [`docs/features/`](features/README.md).

## Design Decisions

- This repo is intentionally a static-site build engine, not a long-running service. That constraint comes both from the product goal and from GitHub Pages as the default publishing target.
- The reusable [`build_site.yaml`](../.github/workflows/build_site.yaml) workflow is a core part of the architecture. Host `comic_git` repos are expected to call this workflow remotely so engine behavior can be centralized and updated for many users at once.
- [`main.yaml`](../.github/workflows/main.yaml) is a maintainer workflow for releasing `comic_git_engine` itself and is not part of the end-user integration surface.
- Host `comic_git` repos should be thought of primarily as user data stores plus a small amount of scaffolding. The engine repo is where the main build logic, defaults, and shared behavior live.
- The user-content model prioritizes minimal technical intimidation. File formats, defaults, and content layout are designed so non-technical creators can work mostly through folders, `.ini` files, `.txt` files, and image assets.
- Runtime dependencies should stay minimal because they are installed during GitHub Actions runs for end-user sites. Developer-only tools should not become required engine runtime dependencies.
