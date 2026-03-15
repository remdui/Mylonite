from dataclasses import dataclass
from typing import Protocol

from .content_loader import PortfolioContentLoader
from mylonite.core.content_types import PersonProfile, SiteConfig
from .view_models import HomeHeroViewModel, HomePageViewModel, LayoutViewModel


@dataclass(frozen=True)
class SharedPageContext:
    site: SiteConfig
    owner: PersonProfile
    layout_context: dict


class PageContextBuilder(Protocol):
    page_name: str

    def build(
        self, shared: SharedPageContext, loader: PortfolioContentLoader
    ) -> dict: ...


class HomePageContextBuilder:
    page_name = "home"

    def build(self, shared: SharedPageContext, loader: PortfolioContentLoader) -> dict:
        hero = HomeHeroViewModel(
            display_name=shared.owner.display_name or shared.owner.full_name,
            headline=shared.owner.headline,
            bio=shared.owner.bio,
            summary=shared.owner.summary,
        )
        page_model = HomePageViewModel(page_title="Home", hero=hero)

        context = dict(shared.layout_context)
        context.update(page_model.to_context())
        return context


class WebPageContextFactory:
    """Builds page contexts from shared content and per-page builders."""

    def __init__(
        self,
        loader: PortfolioContentLoader | None = None,
        builders: dict[str, PageContextBuilder] | None = None,
    ):
        self.loader = loader or PortfolioContentLoader()
        self.builders = builders or {
            HomePageContextBuilder.page_name: HomePageContextBuilder(),
        }

    def _load_shared_context(self) -> SharedPageContext:
        self.loader.begin_tracking()
        site = self.loader.load_site()
        owner = self.loader.load_person(site.owner_id)

        layout = LayoutViewModel(
            site_title=site.site_title,
            site_url=site.site_url,
            footer_show_generated_by=site.footer_show_generated_by,
            footer_repository_url=site.footer_repository_url,
            owner_full_name=owner.full_name,
            content_status=self.loader.build_content_status().to_dict(),
            current_year=self.loader.current_year(),
        )

        layout_context = layout.to_context()
        layout_context["validation_status"] = (
            self.loader.build_validation_status().to_dict()
        )

        return SharedPageContext(
            site=site,
            owner=owner,
            layout_context=layout_context,
        )

    def build_page_context(self, page_name: str) -> dict:
        builder = self.builders[page_name]
        shared = self._load_shared_context()
        return builder.build(shared, self.loader)

    def build_homepage_context(self) -> dict:
        return self.build_page_context(HomePageContextBuilder.page_name)


def build_homepage_context() -> dict:
    return WebPageContextFactory().build_homepage_context()
