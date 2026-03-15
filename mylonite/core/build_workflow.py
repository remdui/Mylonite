from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True)
class BuildInput:
    site_id: str
    content_version: str
    theme_name: str
    artifact_variant: str = ""


def build_cache_key(build_input: BuildInput) -> str:
    raw = (
        f"{build_input.site_id}|{build_input.content_version}|"
        f"{build_input.theme_name}|{build_input.artifact_variant}"
    )
    return sha256(raw.encode("utf-8")).hexdigest()
