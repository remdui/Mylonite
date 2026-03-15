from mylonite.core.content_types import (
    HostingMode,
    PersonProfile,
    SiteConfig,
    SiteInstallSettings,
    ThemeSettings,
)


def map_site_config(site_data: dict) -> SiteConfig:
    theme_data = site_data.get("theme", {})
    install_data = site_data.get("install", {})
    hosting_mode_value = site_data.get("hosting_mode", HostingMode.LOCAL.value)

    try:
        hosting_mode = HostingMode(hosting_mode_value)
    except ValueError:
        hosting_mode = HostingMode.LOCAL

    return SiteConfig(
        site_title=site_data.get("site_title", "Portfolio"),
        site_url=site_data.get("site_url", "http://localhost:8000"),
        owner_id=site_data.get("owner_id", "identity.person.owner"),
        footer_show_generated_by=site_data.get("footer_show_generated_by", True),
        footer_repository_url=site_data.get("footer_repository_url", ""),
        hosting_mode=hosting_mode,
        public_domain=site_data.get("public_domain", ""),
        theme=ThemeSettings(
            name=theme_data.get("name", "default"),
            custom_theme_allowed=theme_data.get("custom_theme_allowed", True),
        ),
        install=SiteInstallSettings(
            setup_wizard_enabled=install_data.get("setup_wizard_enabled", True),
            deferred_setup_allowed=install_data.get("deferred_setup_allowed", True),
        ),
    )


def map_person_profile(object_id: str, entry: dict, bio: str) -> PersonProfile:
    return PersonProfile(
        id=entry.get("id", object_id),
        name=entry.get("name", ""),
        full_name=entry.get("full_name", ""),
        display_name=entry.get("display_name", ""),
        headline=entry.get("headline", ""),
        summary=entry.get("summary", ""),
        bio=bio or entry.get("summary", ""),
        profile_image_path=entry.get("profile_image_path", ""),
    )
