import tomllib
from datetime import date
from pathlib import Path

from django.conf import settings

CONTENT_ROOT = Path(settings.MYLONITE_CONTENT_ROOT)


def example_path(path: Path) -> Path:
    return path.with_name(f"{path.name}.example")


def build_source_info(
    requested_path: Path,
    resolved_path: Path | None = None,
    *,
    used_example: bool = False,
) -> dict:
    return {
        "requested_path": requested_path.relative_to(CONTENT_ROOT).as_posix(),
        "resolved_path": (
            resolved_path.relative_to(CONTENT_ROOT).as_posix() if resolved_path else None
        ),
        "used_example": used_example,
        "missing": resolved_path is None,
    }


def resolve_content_file(path: Path) -> tuple[Path | None, dict]:
    if path.exists():
        return path, build_source_info(path, path, used_example=False)

    fallback = example_path(path)
    if fallback.exists():
        return fallback, build_source_info(path, fallback, used_example=True)

    return None, build_source_info(path)


def load_toml_file(path: Path) -> tuple[dict, dict]:
    resolved_path, source = resolve_content_file(path)
    if resolved_path is None:
        return {}, source

    with resolved_path.open("rb") as handle:
        return tomllib.load(handle), source


def load_text_file(path: Path) -> tuple[str, dict]:
    resolved_path, source = resolve_content_file(path)
    if resolved_path is None:
        return "", source

    return resolved_path.read_text(encoding="utf-8").strip(), source


def load_site_config() -> tuple[dict, list[dict]]:
    data, source = load_toml_file(CONTENT_ROOT / "config" / "site.toml")

    return (
        {
            "site_title": data.get("site_title", "Portfolio"),
            "site_url": data.get("site_url", "http://localhost:8000"),
            "owner_id": data.get("owner_id", "identity.person.owner"),
            "footer_show_generated_by": data.get("footer_show_generated_by", True),
            "footer_repository_url": data.get("footer_repository_url", ""),
        },
        [source],
    )


def load_person(object_id: str) -> tuple[dict, list[dict]]:
    root = CONTENT_ROOT / "entities" / object_id

    entry, entry_source = load_toml_file(root / "entry.toml")
    bio, bio_source = load_text_file(root / "text" / "website.md")

    return (
        {
            "id": entry.get("id", object_id),
            "name": entry.get("name", ""),
            "full_name": entry.get("full_name", ""),
            "display_name": entry.get("display_name", ""),
            "headline": entry.get("headline", ""),
            "summary": entry.get("summary", ""),
            "bio": bio or entry.get("summary", ""),
        },
        [entry_source, bio_source],
    )


def build_content_status(sources: list[dict]) -> dict:
    example_files = [
        source["resolved_path"]
        for source in sources
        if source["used_example"] and source["resolved_path"]
    ]
    missing_files = [source["requested_path"] for source in sources if source["missing"]]

    return {
        "using_example_files": bool(example_files),
        "example_files": example_files,
        "missing_files": missing_files,
    }


def load_portfolio_context() -> dict:
    site, site_sources = load_site_config()
    owner, owner_sources = load_person(site["owner_id"])

    sources = [*site_sources, *owner_sources]

    return {
        "portfolio_site": site,
        "owner_profile": owner,
        "content_status": build_content_status(sources),
        "current_year": date.today().year,
    }
