<!-- ai-agent-toolkit:managed version="1.0.0" -->
<!-- Audience: Developers maintaining repository-local Codex configuration.
     Purpose: Define which .codex files belong to the repository and which remain local runtime state. -->

# Repository-local Codex files

Most of `.codex/` is local Codex runtime state and must not be committed. The
root `.gitignore` therefore ignores the directory by default and explicitly
allows only repository-owned configuration.

## Tracked content

- `rules/default.rules` contains command approvals specific to this repository.
- `skills/<name>/` contains the complete source for each repository-owned skill,
  including any supporting scripts, references, or assets.
- `skills/install-skill-junctions.ps1` registers those skills in the user's
  external `CODEX_HOME` by creating junctions.

When adding a repository-owned skill or rule file, add its exact path to the
`.codex` allowlist in the root `.gitignore`. This deliberate step prevents
generated or installed skills from becoming trackable accidentally.

## Local-only content

Never commit authentication data, installation identifiers, sessions, logs,
memories, goals, SQLite databases, caches, temporary files, plugins, or
generated system skills. In particular, directories such as `.system/`,
`cache/`, `plugins/`, `sessions/`, and `tmp/` are runtime state rather than
repository configuration.

Keep `CODEX_HOME` outside the repository. The junction installer treats this
directory as skill source only and deliberately skips `.system`.
