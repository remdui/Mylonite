# Contributing to Mylonite

Thanks for your interest in contributing.

## How to contribute

- Fork the repository
- Create a branch from `main`
- Make your changes
- Add or update tests and documentation where relevant
- Open a pull request with a clear explanation

## Local development checks

Install dev tooling:

```bash
pip install -e .[dev]
```

Run quality checks before opening a PR:

```bash
ruff check .
ruff format --check .
DJANGO_DEBUG=true python manage.py check --verbosity 2
DJANGO_DEBUG=true python manage.py makemigrations --check --dry-run --verbosity 2
DJANGO_DEBUG=true python manage.py test
```

## Testing

- Centralized test suite lives under `tests/` and mirrors source package structure (for example `tests/apps/panel/` for `apps/panel/`).

### Code coverage

Run tests with coverage and print a terminal summary:

```bash
DJANGO_DEBUG=true coverage run --rcfile=.coveragerc manage.py test
coverage report -m
```

Generate an HTML coverage report:

```bash
coverage html
```

Then open `htmlcov/index.html` in your browser.

## Continuous Integration

- GitHub Actions runs quality checks and the full test suite on pushes to `main` and on pull requests.
- Pull requests also run dependency review checks for newly introduced vulnerable dependencies.
- Secret scanning runs to improve security posture.

## Dependency update PRs

Dependabot opens scheduled dependency update PRs for Python dependencies and GitHub Actions versions.

When reviewing dependency PRs:

- verify CI passes
- scan changelogs for breaking changes
- ensure lockstep updates when multiple related packages change
- merge small safe updates quickly to reduce drift

## Release and versioning

- Mylonite currently follows an alpha release process.
- Version changes are tracked in `pyproject.toml`.
- Any user-visible change should be summarized in the pull request and release notes.
- Breaking changes should be clearly called out in pull requests and releases.

## Guidelines

- Keep changes focused and small where possible
- Follow the existing style and structure
- Update documentation when behavior or setup changes
- Open an issue first for large changes

## Community and support

- `CODE_OF_CONDUCT.md` defines expected behavior.
- `SUPPORT.md` explains where to ask for help.
- `SECURITY.md` defines private vulnerability reporting.

## Licensing

By submitting a contribution, you agree that your contributions are licensed under the AGPLv3 License used by this project.
