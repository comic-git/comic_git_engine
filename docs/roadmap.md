<!-- Audience: Developers and AI agents.
     Purpose: Record larger architectural improvements and migrations that are desirable,
     but not yet approved or scheduled for implementation. -->

# Roadmap

This file tracks larger architectural changes that are likely worth doing but require deliberate planning.

It is not a task backlog. The goal is to capture:

- the desired future state
- why it is desirable
- what makes it risky
- the rough release horizon

## Selective output asset staging

### Current state

`comic_git_engine` now builds into `build/` by default, while retaining an explicit legacy in-place mode. The staged build still copies the complete `your_content/` tree, and deployment mode protects future assets by deleting scheduled source page folders before that copy. Source and public assets are therefore not yet fully separated.

### Desired future state

Source files and generated output should be fully separated:

- source content stays in the host repo
- generated site files remain in the configured output directory
- deployment publishes only that output directory

### Why this is desirable

- It removes the need for destructive cleanup as a publishing safeguard.
- It makes the build model easier to reason about.
- It reduces the risk of accidental local data loss.
- It makes selective publishing easier because the engine can copy only what belongs in the final site.
- It creates a cleaner foundation for future deployment targets.

### Why this is risky

This is a high-risk migration for existing users.

Potential risks include:

- existing themes or hooks relying on arbitrary `your_content/` files being copied
- incomplete asset-reference discovery omitting files that templates or posts need
- local preview and manual-testing workflows assuming the complete source tree is public
- hidden compatibility issues that only appear in long-lived user repos

Because host repos follow patch updates automatically, this must not be introduced as a patch-level behavior change.

### Likely release horizon

`2.0+`

The initial output-directory default is part of 1.1, but selective asset staging remains a separate compatibility-sensitive migration.

### Likely follow-on work

Once selective asset staging is established, the engine should be able to move away from destructive scheduled-post deletion and publish only the files needed for the final site output.

This may also be the point where the output structure itself is redesigned more aggressively. Instead of leaving source-style assets under `your_content/` in the published site, a future build could copy only the required assets into the generated site structure alongside the relevant HTML output.

## Replace destructive scheduled-post deletion with selective publishing

### Current behavior

The current `--delete-scheduled-posts` behavior exists to protect creators from accidentally publishing future comic assets under the legacy root-output model.

That behavior was a rational solution to the original GitHub Pages deployment model, where source files in the repo could end up publicly accessible even if no generated HTML page linked to them.

### Desired future state

With staged output now available, scheduled-post handling should become non-destructive once the engine can selectively copy public assets:

- source files for future comics should remain in the repo
- normal builds should publish only pages and assets whose post date is in the past
- local preview should still support an explicit `--publish-all-comics` mode for checking future pages
- builds should never need to delete source comic folders as part of normal publishing behavior

### Why this is desirable

- It removes a dangerous source-data mutation path from normal development and build workflows.
- It preserves the useful distinction between “build what is public now” and “preview future pages locally.”
- It fits the cleaner output-directory model where publishing is controlled by selective copying, not destructive cleanup.

### Why this is risky

This depends on selective asset staging and should not be attempted as an isolated patch-level cleanup.

Risks include:

- missing files in the final published output if selective copying is incomplete
- changing the effective public URL structure of assets
- breaking existing assumptions in templates, scripts, or themes about where source assets appear in the built site

### Likely release horizon

`2.0+`

This should be treated as a follow-on architectural migration after selective asset staging is established.

## Remove `Allow missing variables in templates`

### Current behavior

`Allow missing variables in templates` disables the default strict Jinja behavior and allows templates to render even when expected variables are missing.

The option exists today, and it has been documented as a valid config option in the end-user docs.

### Desired future state

Remove this option and keep strict template-variable checking as the only supported behavior.

### Why this is desirable

- Strict failures are better for catching real template/data problems early.
- Allowing missing variables weakens error detection and can hide broken or incomplete output.
- The option does not fit the broader product preference for clear, predictable behavior.

### Why this is risky

Because the option is documented, it should be treated as part of the public contract even if it is rarely used.

Risks include:

- breaking sites that currently rely on silent rendering with missing variables
- user confusion if the docs and engine behavior are not updated together

### Likely release horizon

`1.1`

This is a candidate for removal in `1.1`, with matching doc updates and a clear note in release/migration information.

## Harden code hook contracts

### Current behavior

Code hooks are a documented expert feature and part of the public extension surface.

They are already powerful and useful, but the maintainer-facing contract is still mostly implicit in Python call sites and end-user documentation.

### Desired future state

Keep the existing hook system, but make it safer to maintain.

This likely means:

- review the existing hooks one by one instead of redesigning the system broadly
- document hook inputs, outputs, and mutation expectations in developer-facing docs
- add focused automated tests around current hook call points before larger refactors
- tighten hook contracts over time so inputs are more explicit and, where practical, read-only
- prefer explicit return values over mutation where practical, while preserving backward compatibility carefully
- avoid adding new hook points casually
- prefer higher-level config/template/CSS features when they can solve a need without custom Python

### Why this is desirable

- It reduces the risk of refactors accidentally breaking a documented advanced feature.
- It makes hook compatibility more intentional.
- It improves maintainability without forcing a disruptive replacement of the current hook system.

### Why this is risky

Even a hardening pass can accidentally narrow behavior that advanced users currently rely on.

The goal should be to clarify and stabilize the existing surface, not silently redesign it.

### Likely release horizon

`later`

This is an incremental hardening track for a future pass, not immediate `1.1` work and not a major-version architectural migration.
