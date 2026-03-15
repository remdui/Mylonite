from dataclasses import dataclass, field
from enum import StrEnum


class HostingMode(StrEnum):
    LOCAL = "local"
    PUBLIC = "public"


class ArtifactVisibility(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"


@dataclass(frozen=True)
class SourceInfo:
    requested_path: str
    resolved_path: str | None
    used_example: bool
    missing: bool


@dataclass(frozen=True)
class ThemeSettings:
    name: str = "default"
    custom_theme_allowed: bool = True


@dataclass(frozen=True)
class SiteInstallSettings:
    setup_wizard_enabled: bool = True
    deferred_setup_allowed: bool = True


@dataclass(frozen=True)
class SiteConfig:
    site_title: str
    site_url: str
    owner_id: str
    footer_show_generated_by: bool
    footer_repository_url: str
    hosting_mode: HostingMode = HostingMode.LOCAL
    public_domain: str = ""
    theme: ThemeSettings = field(default_factory=ThemeSettings)
    install: SiteInstallSettings = field(default_factory=SiteInstallSettings)


@dataclass(frozen=True)
class PersonProfile:
    id: str
    name: str
    full_name: str
    display_name: str
    headline: str
    summary: str
    bio: str
    profile_image_path: str = ""


@dataclass(frozen=True)
class HomePageContent:
    id: str
    title: str
    markdown: str


@dataclass(frozen=True)
class ValidationStatus:
    has_errors: bool
    errors: list[str]

    def to_dict(self) -> dict:
        return {
            "has_errors": self.has_errors,
            "errors": self.errors,
        }


@dataclass(frozen=True)
class ContentStatus:
    using_example_files: bool
    example_files: list[str]
    missing_files: list[str]

    def to_dict(self) -> dict:
        return {
            "using_example_files": self.using_example_files,
            "example_files": self.example_files,
            "missing_files": self.missing_files,
        }


@dataclass(frozen=True)
class ArtifactDescriptor:
    artifact_id: str
    variant: str
    format: str
    source_profile_id: str
    visibility: ArtifactVisibility
    output_path: str
