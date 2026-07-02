"""Forward-looking artifact service boundaries.

These interfaces are intentionally lightweight: they define the contract for
future CV/document generation without coupling the rest of the application to a
specific backend before that feature is implemented.
"""

from dataclasses import dataclass
from typing import Protocol

from .content_types import ArtifactDescriptor, ArtifactVisibility


@dataclass(frozen=True)
class ArtifactBuildRequest:
    profile_id: str
    variant: str
    output_format: str
    visibility: ArtifactVisibility


class ArtifactGenerator(Protocol):
    """Interface for CV and other artifact generation backends (e.g., TeX)."""

    def generate(self, request: ArtifactBuildRequest) -> ArtifactDescriptor: ...


class ArtifactCatalog(Protocol):
    """Storage/index boundary for public/private artifact lookup and publishing."""

    def save(self, artifact: ArtifactDescriptor) -> None: ...

    def list_for_public_site(self) -> list[ArtifactDescriptor]: ...

    def list_for_dashboard(self) -> list[ArtifactDescriptor]: ...
