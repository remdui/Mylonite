# Mylonite: Your record, refined.

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

1. Copy the local launcher config:

```bash
cp .env.example .env
```

2. Start Mylonite in local mode:

```bash
docker compose -f compose.yaml -f compose.local.yaml up --build
```

3. Open:

```text
http://localhost:8000
```

This mode binds the app only to localhost and is the recommended mode for local development.

#### Initialize editable local content

The repository tracks `.example` content files as defaults and templates.

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
  apps/                 Django apps
  content/              File-based personal records
  infra/docker/         Docker image and other infrastructure artifacts
  mylonite/             Project settings and features
  runtime/config/       Local runtime configs
  runtime/data/         Persistent runtime states
  scripts/              Helper scripts
  static/               Static source files
  templates/            Django website templates
```


## License

Licensed under the GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later). See the `LICENSE` file for details.

