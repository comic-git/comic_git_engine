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
- theme switching is controlled through the TOML or legacy INI comic configuration
- homepage content can be customized through simple content files or through full template override
- many visual assets are user-owned files in `your_content/`, even when the rendering logic comes from the engine

This feature is stable in concept, but it always carries compatibility risk because presentation changes are highly visible and template/JS overrides can stop inheriting engine fixes.

### Structured-image presentation contract

Theme overrides that render structured images follow these presentation rules:

- the comic wrapper uses the `.comic-page` class
- standalone image wrappers use `#comic-image-1`, `#comic-image-2`, and so on
- page-mode archive entries target `#comic-image-1` for image-bearing pages and
  `#post-body` for text-only pages; image-mode entries target their corresponding
  positional image anchor, while tagged entries link without a fragment
- `ComicImage` has no `anchor_id`, and public image records have no `id` or
  `anchor_id`; ordered image position is authoritative
- infinite-scroll image fragments use `#<page-name>_01`, with a minimum of two
  index digits, while bare `#<page-name>` remains an accepted incoming alias

Template and JavaScript replacements are responsible for implementing this
contract because replacement-based overrides do not inherit engine behavior.

### Tagged metadata template context

Engine-rendered comic pages and pages that inherit `comic.tpl`, including
`latest`, receive an authoritative `tagged_pages_enabled` boolean. The engine
derives it independently for each main or Extra Comic from that comic's resolved
`[Pages]` configuration. The built-in template links character and tag values
only when the `tagged` page is configured; otherwise, it renders those values as
plain text.

A theme-owned `comic.tpl` replacement does not inherit that conditional markup,
but it can use `tagged_pages_enabled` to match the built-in behavior. Values
provided by a code hook cannot override this engine-owned flag.

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
