# Themes

Mylonite themes are discovered from subfolders in `themes/`.

Each theme folder must contain:

1. `theme.toml`
2. `static/` directory
3. at minimum, a stylesheet entrypoint at `static/css/site.css`

Only folders that match this format are shown as selectable options in the admin settings page.

## Required metadata

`theme.toml` must contain non-empty values for:

```toml
name = "Theme Name"
description = "What this theme is for."
version = "1.0.0"
```

Folder names must match: `^[a-z0-9][a-z0-9._-]*$`.

## Static-only scope

- Themes do not include Django templates.
- Templates are fixed in `/templates` and shared across all themes.
- A theme controls only static assets under its `static/` folder.

## Fallback behavior

- `default` is the required fallback theme.
- If a selected theme is missing files that exist in `themes/default/static/`,
  Mylonite logs a warning once and serves missing files from default.
- For the main stylesheet entrypoint (`css/site.css`) that exists in both
  selected and default theme, Mylonite serves default CSS first and
  selected-theme CSS second as overrides.

## Example custom theme

```text
themes/
  my-theme/
    theme.toml
    static/
      css/
        site.css
```

After adding a valid theme folder, refresh `Admin -> Settings` and it will appear in the theme selector automatically.
