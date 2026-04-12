<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: AI agents and new contributors.
     Purpose: Define domain-specific terminology used in this codebase and docs.
     Only include terms that are specific to comic_git or this repo's workflow. -->

# Glossary

**comic_git** - The user-facing webcomic project template repo that creators clone or fork to build their own site. It acts mostly as a data store and minimal scaffold around `comic_git_engine`.

**comic_git_docs** - The separate repo that contains end-user documentation. Developer-facing docs belong in `comic_git_engine`; end-user docs should usually be updated there near release time.

**comic_git_engine** - The core build engine repo. It is loaded into a host `comic_git` repo and turns that repo's `your_content/` files into a static website.

**comic_git_dev** - The maintainer's main development and manual-test host repo for engine work. It is commonly used to validate real builds before release.

**Extra Comic** - A secondary comic hosted inside the same site, under its own subdirectory, with its own `comic_info.ini` and `comics/` folder structure.

**Host repo** - A `comic_git` repo that loads `comic_git_engine`, usually by submodule or symlink, and provides the `your_content/` input data the engine builds from.

**Main comic** - The root comic in a host repo, as distinct from any Extra Comics.

**Patch release** - A release that end-user host repos normally receive automatically. In this project, patch releases must never break backward compatibility.

**Reusable workflow** - The GitHub Actions workflow in [`.github/workflows/build_site.yaml`](../.github/workflows/build_site.yaml) that host repos call remotely via `uses: ...`. This is part of the product surface, not just internal CI.

**Theme hook** - A Python extension point in a host repo theme that can alter build behavior. Hook dependencies are optional and separate from the normal engine runtime requirements.

**v1 tag** - The reusable-workflow tag used by host repos when they reference `build_site.yaml`. This is separate from the engine's version branches and tags, and matters during release/rollback thinking.

**your_content** - The top-level input directory in a host repo. It contains user data such as `comic_info.ini`, comic pages, images, themes, transcripts, and Extra Comic folders.
