from dataclasses import dataclass


@dataclass(frozen=True)
class LayoutViewModel:
    site_title: str
    site_url: str
    footer_show_generated_by: bool
    footer_repository_url: str
    owner_full_name: str
    content_status: dict
    current_year: int

    def to_context(self) -> dict:
        return {
            "portfolio_site": {
                "site_title": self.site_title,
                "site_url": self.site_url,
                "footer_show_generated_by": self.footer_show_generated_by,
                "footer_repository_url": self.footer_repository_url,
            },
            "owner_profile": {
                "full_name": self.owner_full_name,
            },
            "content_status": self.content_status,
            "current_year": self.current_year,
        }


@dataclass(frozen=True)
class HomeHeroViewModel:
    display_name: str
    headline: str
    bio: str
    intro_markdown: str
    summary: str

    def to_context(self) -> dict:
        return {
            "display_name": self.display_name,
            "headline": self.headline,
            "bio": self.bio,
            "intro_markdown": self.intro_markdown,
            "summary": self.summary,
        }


@dataclass(frozen=True)
class HomePageViewModel:
    page_title: str
    hero: HomeHeroViewModel

    def to_context(self) -> dict:
        return {
            "page_title": self.page_title,
            "home_page": {
                "hero": self.hero.to_context(),
            },
        }
