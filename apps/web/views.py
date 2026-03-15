import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import FileResponse
from django.http import Http404
from django.http import JsonResponse
from django.http import HttpResponse
from django.views.generic import TemplateView, View

from mylonite.core.theme_loader import (
    ResolvedTheme,
    ThemeResolver,
    load_active_theme_settings,
    normalize_theme_asset_path,
)

from .page_contexts import HomePageContextBuilder, WebPageContextFactory


class HealthView(View):
    def get(self, request):
        return JsonResponse({"status": "ok"})


class PageContextTemplateView(TemplateView):
    template_name = ""
    page_name = ""
    context_factory_class = WebPageContextFactory

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context_factory = self.context_factory_class()
        context.update(context_factory.build_page_context(self.page_name))
        return context


class HomePageView(PageContextTemplateView):
    template_name = "web/home.html"
    page_name = HomePageContextBuilder.page_name


class ThemeStaticView(View):
    primary_css_asset_path = "css/site.css"

    def _build_css_response(
        self,
        *,
        resolved_theme: ResolvedTheme,
        normalized_path: str,
        active_css_path: Path,
    ) -> HttpResponse | None:
        if normalized_path != self.primary_css_asset_path:
            return None

        if (
            resolved_theme.active_theme.theme_id
            == resolved_theme.default_theme.theme_id
        ):
            return None

        default_css_path = resolved_theme.default_theme.static_dir / normalized_path
        if not default_css_path.is_file():
            return None

        try:
            default_css = default_css_path.read_text(encoding="utf-8")
            active_css = active_css_path.read_text(encoding="utf-8")
        except OSError:
            return None

        merged_css = (
            f"{default_css}\n\n"
            f"/* Theme overrides ({resolved_theme.active_theme.theme_id}) */\n"
            f"{active_css}\n"
        )
        response = HttpResponse(merged_css, content_type="text/css; charset=utf-8")
        response["Cache-Control"] = "no-cache"
        return response

    def get(self, request, asset_path: str):
        normalized_path = normalize_theme_asset_path(asset_path)
        if not normalized_path:
            raise Http404("Invalid theme asset path.")

        resolver = ThemeResolver(Path(settings.MYLONITE_THEMES_ROOT))
        discovered_themes = resolver.discover_themes()
        theme_settings = load_active_theme_settings(
            content_root=Path(settings.MYLONITE_CONTENT_ROOT)
        )
        resolved_theme = resolver.resolve(theme_settings, themes=discovered_themes)
        resolved_asset = resolver.resolve_static_asset(
            resolved_theme,
            asset_path=normalized_path,
        )
        if resolved_asset is None:
            raise Http404("Theme asset not found.")

        if (
            normalized_path.endswith(".css")
            and not resolved_asset.from_fallback
        ):
            css_response = self._build_css_response(
                resolved_theme=resolved_theme,
                normalized_path=normalized_path,
                active_css_path=resolved_asset.resolved_path,
            )
            if css_response is not None:
                return css_response

        content_type, _ = mimetypes.guess_type(resolved_asset.resolved_path.as_posix())
        response = FileResponse(
            resolved_asset.resolved_path.open("rb"),
            content_type=content_type or "application/octet-stream",
        )
        response["Cache-Control"] = "no-cache"
        return response


health = HealthView.as_view()
home = HomePageView.as_view()
theme_static = ThemeStaticView.as_view()
