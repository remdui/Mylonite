# Default Theme

This is the built-in theme shipped with Mylonite.
It is the canonical fallback for all theme assets.

## Metadata

`theme.toml` declares:

- `name`: human-readable theme name
- `description`: short explanation shown in admin settings
- `version`: theme version

## Assets

- Main stylesheet entrypoint: `static/css/site.css`
- Static-only theme contract: all theme files must live under `static/`
- Template files are not part of the theme system

## How fallback works

- Mylonite always resolves missing theme assets from `themes/default/static/`
- For the main stylesheet (`css/site.css`), Mylonite serves default CSS first, then selected-theme CSS as overrides
- This keeps default styling values in place for anything not overridden by the custom theme

## Required metadata file

`theme.toml` must contain non-empty values:

```toml
name = "Default"
description = "Built-in Mylonite theme with the standard visual style."
version = "1.0.0"
```
