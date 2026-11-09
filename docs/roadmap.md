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

`comic_git_engine` builds into `build/` by default, while retaining legacy in-place mode. In 1.1.1, opt-in [folder-level selective staging](features/content-staging/) copies only eligible page folders and preserves arbitrary auxiliary content. Native local SFTP enables it by default. Existing builds retain wholesale copying and scheduled-source deletion when requested. Thumbnail generation remains a committable source cache; selected source metadata remains public.

### Desired future state

Source inputs and published output should be clearly separated, while retaining
intentional committable thumbnail caches:

- source content stays in the host repo
- generated site files remain in the configured output directory
- deployment publishes only that output directory
- stage only explicitly public assets instead of copying all of `your_content/`
- exclude original INI/TOML source files by default; if compatibility requires public info files, generate sanitized copies with `!`-prefixed private values removed, leaving source files unchanged
- verify private values are absent from every published representation, not only `page_info_list.json`

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

Because host repos follow patch updates automatically, changing the default or excluding source info files must not be introduced as an automatic patch-level behavior change. The opt-in 1.1.1 mode provides real-world testing without that default switch.

### Likely release horizon

`2.0+`

The output-directory default is part of 1.1 and folder-level staging is opt-in in 1.1.1. Source-info exclusion, reference-based selection, and changing defaults remain separate compatibility-sensitive migrations.

### Likely follow-on work

Use experience with opt-in staging to evaluate changing the default and eventually retiring destructive scheduled-post deletion. Do not conflate that change with excluding source metadata or redesigning asset URLs.

This may also be the point where the output structure itself is redesigned more aggressively. Instead of leaving source-style assets under `your_content/` in the published site, a future build could copy only the required assets into the generated site structure alongside the relevant HTML output.

## Modernize analytics integration

### Current behavior

comic_git retains a simple Google Analytics compatibility feature: when a value is set in the legacy `[Google Analytics]` `Tracking ID` option or the TOML `analytics.google_analytics_id` key, templates load Google's tag on every generated page.

The basic tag shape remains compatible with Google Analytics 4, but the integration has no ID validation or consent handling. It also uses legacy configuration terminology, and bundled or user-owned base-template overrides can duplicate the tag markup.

### Desired future state

Treat analytics as an intentional, privacy-aware feature rather than a snippet enabled by one unexplained value:

- use current Google tag terminology and clearly define the supported tag-ID contract
- preserve existing configuration as a carefully documented compatibility alias
- diagnose obsolete Universal Analytics `UA-` IDs and malformed values
- validate and safely render configured IDs
- provide a conservative consent experience that does not load the tag before consent by default
- let visitors decline analytics, remember their choice, and change it later
- keep privacy text and a privacy-information link customizable without implying guaranteed legal compliance
- build on a site-wide cookie and browser-storage consent model rather than creating analytics-only controls
- centralize the generated markup and test the default and bundled-theme behavior
- expose the feature through a future CMS only when the generated-site behavior is ready

### Why this is desirable

- Current Universal Analytics examples no longer work with Google's supported analytics product.
- A bare tag ID does not address modern consent and disclosure expectations.
- comic_git's non-technical users should not need to design their own consent system before they can use a documented feature responsibly.
- Centralizing and testing the integration reduces drift between default and bundled themes.

### Why this is risky

Consent and disclosure requirements vary by location and can change over time. A built-in interface must therefore be conservative, customizable, accessible, and clear about the site owner's responsibilities without presenting itself as legal advice.

Changing configuration or template behavior also affects existing sites, including custom themes and users who already provide their own consent-management solution. Compatibility and override behavior need an explicit design before implementation.

### Likely release horizon

`later`

This is intentionally not assigned to a version. It may ship alongside the planned CMS because the CMS is a natural place for approachable configuration, but the generated-site consent behavior should remain independent and should not be blocked indefinitely on the CMS.

## Add site-wide cookie and browser-storage consent handling

### Current behavior

The engine has generic JavaScript helpers for reading and writing cookies, but it does not have a central inventory of browser storage or a site-wide consent interface. The current transcript-language selector does not persist its selection; any future transcript preference, analytics consent choice, or similar state would need to define its own storage behavior.

### Desired future state

Provide one small, reusable privacy and preference layer for features that use cookies or browser storage:

- inventory engine-owned cookies, local storage, and third-party storage behavior
- distinguish strictly necessary state, user-requested preferences, analytics, and any future categories that materially need different handling
- document necessary storage clearly even when it does not require an opt-in choice
- ask before enabling non-essential storage or third-party measurement by default
- persist consent choices and make them easy to review, change, or clear
- let a transcript-language preference or similar convenience setting be saved only after an intentional user interaction
- give themes accessible extension points without requiring each theme to recreate consent logic
- keep the generated site usable when all optional storage is declined or unavailable

### Why this is desirable

- It prevents each feature from inventing a different banner, preference format, or cookie policy.
- It gives non-technical creators one understandable place to configure privacy-related behavior.
- It makes future analytics support and small quality-of-life preferences easier to test and explain.

### Why this is risky

Not every cookie or stored preference has the same legal or product requirements, and those requirements vary by location. Treating all storage identically could produce confusing prompts, while treating too much as necessary could undermine meaningful consent.

Existing themes and custom JavaScript may also set their own storage outside engine control. The built-in interface should accurately describe what comic_git manages without claiming to audit arbitrary user customizations or guarantee legal compliance.

### Likely release horizon

`later`

Plan this alongside the analytics modernization and CMS configuration work, while keeping the generated-site implementation independently usable.

## Replace destructive scheduled-post deletion with selective publishing

### Current behavior

The legacy `--delete-scheduled-posts` behavior exists to protect creators from accidentally publishing future comic assets under the root-output model. The opt-in 1.1.1 staging mode already protects that boundary by omitting scheduled page folders from output while preserving their sources.

That behavior was a rational solution to the original GitHub Pages deployment model, where source files in the repo could end up publicly accessible even if no generated HTML page linked to them.

### Desired future state

The remaining work is to make non-destructive selective copying the default,
using evidence from the opt-in mode and an explicit compatibility decision:

- source files for future comics should remain in the repo
- normal builds should publish only pages and assets whose post date is in the past
- local preview should still support an explicit `--publish-all-comics` mode for checking future pages
- builds should never need to delete source comic folders as part of normal publishing behavior

### Why this is desirable

- It removes a dangerous source-data mutation path from normal development and build workflows.
- It preserves the useful distinction between “build what is public now” and “preview future pages locally.”
- It fits the cleaner output-directory model where publishing is controlled by selective copying, not destructive cleanup.

### Why this is risky

The 1.1.1 opt-in mode already avoids destructive deletion by selecting whole page folders. Replacing the legacy default remains a compatibility-sensitive change; reference-based asset selection is not a prerequisite for non-destructive folder staging.

Risks include:

- missing files in the final published output if selective copying is incomplete
- changing the effective public URL structure of assets
- breaking existing assumptions in templates, scripts, or themes about where source assets appear in the built site

### Likely release horizon

`2.0+`

The future default switch should use evidence from the opt-in mode and explicit migration guidance. Existing legacy defaults remain supported in 1.1.1.

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
