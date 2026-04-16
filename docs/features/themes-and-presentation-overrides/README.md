<!-- ai-agent-toolkit:managed version="1.0.0" -->

# Themes and presentation overrides

| Field      | Value    |
|------------|----------|
| **Status** | `active` |

## Summary

This feature covers how comic_git sites change their presentation without changing the core engine.

It includes themes, template overrides, CSS customization, JavaScript replacement, and user-owned presentation assets such as banners, fonts, navigation icons, and homepage content.

## Current State & Roadmap

The current model deliberately uses different customization strategies for different asset types:

- CSS is layered so users can customize styles incrementally
- templates are primarily override-based
- JavaScript is also primarily override-based

This allows unmodified or partially modified sites to keep benefiting from engine CSS fixes, while still giving advanced users full control when they need to replace templates or scripts.

Important current behavior:

- the default theme is a normal theme and can be edited directly in the host repo
- theme switching is controlled through `comic_info.ini`
- homepage content can be customized through simple content files or through full template override
- many visual assets are user-owned files in `your_content/`, even when the rendering logic comes from the engine

This feature is stable in concept, but it always carries compatibility risk because presentation changes are highly visible and template/JS overrides can stop inheriting engine fixes.

## Product Rules

- Presentation customization should be approachable at multiple levels, from simple CSS edits to full template replacement.
- CSS should remain the preferred path for piecemeal visual customization.
- Templates and JavaScript should be treated as heavier override points with higher maintenance cost.
- User-owned theme files must survive engine updates.
- Refactors in this area should be reviewed for their effect on overridden templates, layered CSS behavior, and theme portability.

## Supporting Documents

| Document | Contents |
|----------|----------|
| [../../decisions/2026-04-12-css-layering-vs-template-and-js-overrides.md](../../decisions/2026-04-12-css-layering-vs-template-and-js-overrides.md) | Why CSS is layered while templates and JavaScript are primarily override-based |
| [../../decisions/2026-04-12-engine-and-host-repo-boundary.md](../../decisions/2026-04-12-engine-and-host-repo-boundary.md) | Why default presentation logic stays in `comic_git_engine` while user customizations live in the host repo |
