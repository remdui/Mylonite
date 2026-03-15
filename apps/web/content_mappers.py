from mylonite.core.content_conventions import DEFAULT_OWNER_ID
from mylonite.core.content_schema import (
    HOMEPAGE_CONTENT_SCHEMA,
    PERSON_PROFILE_SCHEMA,
    SITE_CONFIG_SCHEMA,
    schema_defaults,
)
from mylonite.core.content_types import (
    HomePageContent,
    HostingMode,
    PersonProfile,
    SiteConfig,
    SiteInstallSettings,
    ThemeSettings,
)


def map_site_config(site_data: dict) -> SiteConfig:
    defaults = schema_defaults(SITE_CONFIG_SCHEMA)
    merged_site_data = {**defaults, **site_data}
    theme_data = merged_site_data.get("theme", {})
    install_data = merged_site_data.get("install", {})
    hosting_mode_value = merged_site_data.get("hosting_mode", HostingMode.LOCAL.value)

    try:
        hosting_mode = HostingMode(hosting_mode_value)
    except ValueError:
        hosting_mode = HostingMode.LOCAL

    return SiteConfig(
        site_title=merged_site_data.get("site_title", "Portfolio"),
        site_url=merged_site_data.get("site_url", "http://localhost:8000"),
        owner_id=merged_site_data.get("owner_id", DEFAULT_OWNER_ID),
        footer_show_generated_by=merged_site_data.get("footer_show_generated_by", True),
        footer_repository_url=merged_site_data.get("footer_repository_url", ""),
        hosting_mode=hosting_mode,
        public_domain=merged_site_data.get("public_domain", ""),
        theme=ThemeSettings(
            name=theme_data.get("name", "default"),
            custom_theme_allowed=theme_data.get("custom_theme_allowed", True),
        ),
        install=SiteInstallSettings(
            setup_wizard_enabled=install_data.get("setup_wizard_enabled", True),
            deferred_setup_allowed=install_data.get("deferred_setup_allowed", True),
        ),
    )


def map_person_profile(object_id: str, entry: dict, _: str) -> PersonProfile:
    defaults = schema_defaults(PERSON_PROFILE_SCHEMA)
    merged_entry = {**defaults, **entry}

    return PersonProfile(
        id=merged_entry.get("id", object_id),
        name=merged_entry.get("name", ""),
        full_name=merged_entry.get("full_name", ""),
        display_name=merged_entry.get("display_name", ""),
        headline=merged_entry.get("headline", ""),
        summary=merged_entry.get("summary", ""),
        bio=merged_entry.get("summary", ""),
        profile_image_path=merged_entry.get("profile_image_path", ""),
    )


def map_homepage_content(object_id: str, entry: dict, markdown: str) -> HomePageContent:
    defaults = schema_defaults(HOMEPAGE_CONTENT_SCHEMA)
    merged_entry = {**defaults, **entry}
    return HomePageContent(
        id=merged_entry.get("id", object_id),
        title=merged_entry.get("title", "Homepage Main Content"),
        markdown=markdown or merged_entry.get("markdown", ""),
    )
