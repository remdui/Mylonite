This directory is the canonical content tree for a Mylonite site.

## How it works

For each content file, Mylonite uses this resolution rule:

1. use the real file if it exists
2. otherwise use the matching `.example` file

Examples:

- `config/site.toml`
- `config/site.toml.example`

- `entities/identity.person.owner/entry.toml`
- `entities/identity.person.owner/entry.toml.example`

- `entities/identity.person.owner/text/website.md`
- `entities/identity.person.owner/text/website.md.example`

## Git behavior

- real local content files are ignored by git
- tracked `*.example` files provide defaults and templates

## Creating editable local files

Run:

```bash
./scripts/init-content.sh
```
