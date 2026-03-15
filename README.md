# Mylonite: Your record, refined.

[![Status: Alpha](https://img.shields.io/badge/status-alpha-orange)](https://github.com/remdui/mylonite)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License: AGPL v3+](https://img.shields.io/badge/license-AGPLv3%2B-blue.svg)](LICENSE)
[![CI](https://github.com/remdui/mylonite/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/remdui/mylonite/actions/workflows/ci.yml)
[![Dependency Review](https://github.com/remdui/mylonite/actions/workflows/dependency-review.yml/badge.svg)](https://github.com/remdui/mylonite/actions/workflows/dependency-review.yml)
[![Last commit](https://img.shields.io/github/last-commit/remdui/mylonite?logo=github)](https://github.com/remdui/mylonite/commits/main)
[![Open issues](https://img.shields.io/github/issues/remdui/mylonite)](https://github.com/remdui/mylonite/issues)
[![Open pull requests](https://img.shields.io/github/issues-pr/remdui/mylonite)](https://github.com/remdui/mylonite/pulls)



One source of truth that turns your records into a portfolio, homepage, tailored CVs, transcripts, and supporting documents.

---

## Status

**Alpha version.**

Mylonite is currently in active development.


## Why Mylonite?

Mylonite is a rock formed deep underground by intense, sustained pressure. Unlike other rocks, it is not shattered by this pressure; it is transformed by it. Under the right conditions, scattered minerals are refined into a finer, more coherent structure that preserves both movement and identity.

That is the philosophy behind this platform.

A professional life is built under pressure: through education, projects, setbacks, specialization, and reinvention. Usually, that history lives as fragments: transcripts, CV drafts, old portfolios, notes, documents, achievements, and records that rarely exist in one place. Mylonite is where that material is maintained, organized, and refined into a single source of truth.

The name is particularly fitting because mylonite comes from the Greek word for "mill". This platform is not just a repository, it is a refining system. It turns individual records into structure: a personal homepage, tailored CVs, academic records, supporting documents, and a portfolio that all derive from the same maintained core.

Just as mylonite preserves its strongest minerals even as the rock around them changes, this system is built to preserve what matters most: your values, your intellectual identity, your contributions. You can adapt your story for any context without losing the truth of how you got there.

**Mylonite is a record of pressure made coherent.**

## What Mylonite is for

Mylonite is meant for people who want a polished, technically credible, academically professional online presence without maintaining the same information in many different places.

The intended end state is a platform that can generate and maintain, from one source of truth:

- a personal homepage
- an about page
- projects and work experience
- research interests and themes
- professional links and contact details
- blog content
- downloadable documents
- multiple tailored CV variants
- transcripts, certificates, thesis files, and supporting artifacts

The core idea is simple:

> maintain your record once, and derive everything else from it.

## Running Mylonite

### Requirements

To run the current alpha version, you need:

- Docker
- Docker Compose

The current version is designed to run as a single application container by default.


### First run behavior

On first start, Mylonite will:

- start the Django application
- create local runtime state in `runtime/`
- automatically generate `runtime/config/.env` with a unique Django secret key if needed
- use the tracked `.example` content files when no real local content files are present

This means the current alpha version should run out of the box without requiring manual secret generation or content bootstrapping.


### Option 1: Run locally

1. Start Mylonite in local mode:

```bash
docker compose -f compose.yaml -f compose.local.yaml up --build
```

2. Open:

```text
http://localhost:8000
```

This mode binds the app only to localhost and is the recommended mode for local development.

Optional overrides:

- If you want to customize bind paths, port, or runtime UID/GID mapping, copy `.env.example` to `.env` and adjust values.
- On Linux, leave `MYLONITE_PUID/MYLONITE_PGID` at `1000` unless your user/group IDs are different.
- Theme folders are bind-mounted from `./themes` by default (`MYLONITE_THEMES_DIR`).

#### Initialize editable local content

Example content files are generated from the schema automatically at startup and are intentionally not tracked in git.

If you want to create editable content files in `content/` without overwriting anything that already exists, run:

```bash
./scripts/init-content.sh
```

After that, edit the content files in `content/`.


### Option 2: Run behind a reverse proxy (Recommended)

Mylonite also supports running behind a reverse proxy such as Caddy.

The reverse-proxy Compose mode assumes there is already an external Docker network called `proxy`.

Create it once if needed:

```bash
docker network create proxy
```

Then start Mylonite in reverse-proxy mode:

```bash
docker compose -f compose.yaml -f compose.reverse-proxy.yaml up -d --build
```

In this mode, the Mylonite container is attached to the shared `proxy` network and is not exposed directly through a localhost port binding.

For real deployments, place your production settings in `runtime/config/deploy.toml` (for example by copying `runtime/config/deploy.toml.example`). This file remains outside the image so deployment-specific security and domain settings stay versioned per instance.

#### Example Caddy configuration

If Caddy is running in Docker on the same external `proxy` network, it can proxy traffic directly to the Mylonite container by service name.

Example Caddyfile:

```caddy
example.com {
    encode zstd gzip
    reverse_proxy app:8000
}
```

Important notes:

- the Caddy container must also be attached to the same external `proxy` network
- the Mylonite service name is `app`, so the upstream is `app:8000`
- this is the recommended public-facing deployment model for the current version


## Current capabilities

The current alpha version includes:

- a containerized Django-based application server
- a file-based content tree under `content/`
- a homepage rendered from content files
- a local run mode and a reverse-proxy mode


## Planned functionality

Planned functionality includes:

- a richer structured content model
- additional website pages
- portfolio sections for projects, experience, education, and downloads
- artifact generation
- multiple CV variants
- TeX-based PDF generation
- public/private artifact handling
- a blog platform
- more complete site configuration
- stronger admin and operational tooling
- improved validation, caching, and build workflows


## Design principles

Mylonite is being built around the following principles:

- **one source of truth**
- **single-container deployment by default**
- **simple upgrade paths**
- **structured long-term maintainability**
- **clean separation between code, content, config, and runtime data**
- **open-source design**
- **ownership of data**


## Project structure

A simplified overview of the current structure:

```text
Mylonite/
  apps/                 Django apps (web, panel)
  content/              File-based personal records
  infra/docker/         Docker image and other infrastructure artifacts
  mylonite/             Project settings and shared core modules
  mylonite/core/        Reusable domain and workflow primitives
  runtime/config/       Local runtime configs
  runtime/data/         Persistent runtime states
  scripts/              Helper scripts
  themes/               Theme folders and static theme assets
  templates/            Django website templates
```


## Community

- [Contributing guide](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security policy](SECURITY.md)
- [Support](SUPPORT.md)

## License

Licensed under the GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later). See the `LICENSE` file for details.
