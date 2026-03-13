# Contributing to Mylonite

Thanks for your interest in contributing.

## How to contribute

- Fork the repository
- Create a branch from `main`
- Make your changes
- Add or update tests and documentation where relevant
- Open a pull request with a clear explanation

## Testing

- Centralized test suite lives under `tests/` and mirrors source package structure (for example `tests/apps/panel/` for `apps/panel/`).
- Run all tests with:

```bash
DJANGO_DEBUG=true python manage.py test
```

### Code coverage

Install dev tooling (includes `coverage`):

```bash
pip install -e .[dev]
```

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



## Guidelines

- Keep changes focused and small where possible
- Follow the existing style and structure
- Update documentation when behavior or setup changes
- Open an issue first for large changes

## Licensing

By submitting a contribution, you agree that your contributions are licensed under the AGPLv3 License used by this project.
