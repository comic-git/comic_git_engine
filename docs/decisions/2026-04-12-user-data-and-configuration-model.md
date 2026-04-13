<!-- ai-agent-toolkit:managed version="1.0.0" -->

# User data and configuration model

| Field             | Value      |
|-------------------|------------|
| **Date**          | 2026-04-12 |
| **Status**        | `active`   |
| **Supersedes**    |            |
| **Superseded by** |            |

## Context

comic_git is aimed at non-technical users, especially Windows users who are most comfortable working with folders, image files, and text files they can open directly from Explorer.

More structured or more automated approaches are possible, but they raise the support burden:

- databases require extra setup
- JSON/YAML are less forgiving and harder to troubleshoot
- large config files increase cognitive load
- hidden magic makes behavior harder to understand and debug

## Decision

Keep the user-facing data model simple, file-based, and conservative.

- User content lives in `your_content/` as folders, images, INI files, TXT files, and similar simple assets.
- Prefer INI and TXT for user-editable config/content because they open easily on Windows and are forgiving to edit.
- Keep `comic_info.ini` intentionally small. Only surface options users are likely to change often.
- Advanced options should usually exist as hidden defaults with documentation, not as visible defaults in the sample config.
- Favor safe, understandable defaults over clever automation or hidden behavior.

## Consequences

This keeps the first-run and ongoing editing experience approachable for non-technical users.

It also means:

- some capabilities are less discoverable unless docs are maintained well
- developers should resist “just add another visible option” unless it clearly reduces user friction
- data and config changes should be judged partly by how easy they are to edit with plain Windows tools

## Files Affected

- `your_content/`
- `scripts/utils.py`
- `scripts/build_site.py`
- `scripts/rss.py`
- `templates/`
- `default_files/`
- `docs/architecture.md`
- `docs/coding-principles.md`
- `docs/glossary.md`
