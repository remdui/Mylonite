This directory is the canonical content tree for a Mylonite site.

## How it works

For each content file, Mylonite uses this resolution rule:

1. use the real file if it exists
2. otherwise use the matching `.example` file

Example files are generated and synchronized automatically from schema definitions when the app starts. These generated files are intentionally not tracked in git.

## Entity naming conventions

- Use dotted ids to namespace entities by domain and purpose (examples: `identity.person.owner`, `content.homepage.main`).
- Keep one entity per folder under `content/entities/<entity_id>/`.
- Put structured fields in `entry.toml` and large markdown bodies in `text/<name>.md`.

Examples:

- `config/site.toml`
- `config/site.toml.example`

- `entities/identity.person.owner/entry.toml`
- `entities/identity.person.owner/entry.toml.example`

- `entities/content.homepage.main/text/main.md`
- `entities/content.homepage.main/text/main.md.example`

## Git behavior

- real local content files are ignored by git
- generated local `*.example` files provide defaults and templates

## Creating editable local files

Run:

```bash
./scripts/init-content.sh
```

This creates editable local copies from the generated examples without overwriting existing files.


## Extending entities in code

Entity behavior is defined in `apps/web/content_registry.py` with:

- a schema (validation + defaults),
- a mapper (domain projection),
- a body source strategy (`NoBodySourceSpec` or `FieldBodySourceSpec`).

This keeps path conventions and loading logic centralized while allowing future entities (projects, jobs, CV records) to reuse the same scaffolding and loading flow.
