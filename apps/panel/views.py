from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import FormView, TemplateView

from pathlib import Path

from mylonite.core.site_config_store import (
    load_site_config_payload,
    write_site_config_payload,
)
from mylonite.core.theme_loader import ThemeResolver, load_active_theme_settings

from .forms import (
    OwnerSetupForm,
    PanelAuthenticationForm,
    PanelPasswordChangeForm,
    ThemeSelectionForm,
)
from .models import SiteSetup
from .services import (
    InitialSetupAlreadyComplete,
    owner_setup_lock,
    panel_is_initialized,
    user_is_owner,
)


class PanelInitializedMixin:
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not panel_is_initialized():
            return redirect("panel:setup")
        return super().dispatch(request, *args, **kwargs)


class SetupOnlyMixin:
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if panel_is_initialized():
            return redirect("panel:root")
        return super().dispatch(request, *args, **kwargs)


class OwnerRequiredMixin:
    login_url = reverse_lazy("panel:login")

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not panel_is_initialized():
            return redirect("panel:setup")

        if not request.user.is_authenticated:
            return redirect(f"{self.login_url}?next={request.get_full_path()}")

        if not user_is_owner(request.user):
            raise PermissionDenied(
                "You do not have access to this administrative panel."
            )

        return super().dispatch(request, *args, **kwargs)


class PanelContextMixin:
    panel_section = ""
    panel_heading = ""
    panel_description = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("page_title", self.panel_heading or "Admin")
        context["panel_section"] = self.panel_section
        context["panel_heading"] = self.panel_heading
        context["panel_description"] = self.panel_description
        return context


class AdminRootView(View):
    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not panel_is_initialized():
            return redirect("panel:setup")
        if request.user.is_authenticated and user_is_owner(request.user):
            return redirect("panel:dashboard")
        return redirect("panel:login")


class SetupView(SetupOnlyMixin, PanelContextMixin, FormView):
    template_name = "panel/setup.html"
    form_class = OwnerSetupForm
    panel_heading = "Initialize Mylonite"
    panel_description = (
        "Create the owner account that will be used to access the Mylonite "
        "administrative panel."
    )

    def form_valid(self, form):
        try:
            with owner_setup_lock():
                with transaction.atomic():
                    setup = SiteSetup.get_solo()

                    if setup.is_initialized:
                        raise InitialSetupAlreadyComplete

                    user = form.save()
                    setup.owner = user
                    setup.completed_at = timezone.now()
                    setup.save(update_fields=["owner", "completed_at", "updated_at"])
        except InitialSetupAlreadyComplete:
            form.add_error(
                None,
                "Initial setup has already been completed for this instance.",
            )
            return self.form_invalid(form)
        except IntegrityError:
            form.add_error(
                None,
                "The owner account could not be created. Please try again.",
            )
            return self.form_invalid(form)

        login(
            self.request,
            user,
            backend="django.contrib.auth.backends.ModelBackend",
        )
        self.request.session["mylonite_setup_complete"] = True
        messages.success(self.request, "Owner account created successfully.")
        return redirect("panel:setup_complete")


class SetupCompleteView(OwnerRequiredMixin, PanelContextMixin, TemplateView):
    template_name = "panel/setup_complete.html"
    panel_heading = "Setup complete"
    panel_description = (
        "Mylonite has been initialized and the owner account is ready to use."
    )

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not request.session.pop("mylonite_setup_complete", False):
            return redirect("panel:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["admin_panel_url"] = self.request.build_absolute_uri(
            reverse("panel:dashboard")
        )
        context["homepage_url"] = reverse("home")
        return context


class PanelLoginView(PanelInitializedMixin, PanelContextMixin, auth_views.LoginView):
    template_name = "panel/login.html"
    authentication_form = PanelAuthenticationForm
    redirect_authenticated_user = True
    panel_heading = "Sign in"
    panel_description = "Access the Mylonite administrative panel."

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if request.user.is_authenticated and user_is_owner(request.user):
            return redirect("panel:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return self.get_redirect_url() or reverse("panel:dashboard")


class PanelLogoutView(PanelInitializedMixin, auth_views.LogoutView):
    next_page = reverse_lazy("home")


class PanelDashboardView(OwnerRequiredMixin, PanelContextMixin, TemplateView):
    template_name = "panel/dashboard.html"
    panel_section = "dashboard"
    panel_heading = "Dashboard"
    panel_description = (
        "This is the administrative control panel for your Mylonite instance. "
        "Here you will manage and maintain your source of truth: the records, "
        "settings, and structured content that define your professional profile. "
        "From this panel, Mylonite will grow to support editing entities, managing "
        "public pages, validating data, and generating output artifacts such as CVs, "
        "supporting documents, and other portfolio materials."
    )


class PanelSettingsView(OwnerRequiredMixin, PanelContextMixin, TemplateView):
    template_name = "panel/settings.html"
    panel_section = "settings"
    panel_heading = "Settings"
    panel_description = "Update your owner account credentials and theme."

    @property
    def _content_root(self) -> Path:
        return Path(settings.MYLONITE_CONTENT_ROOT)

    @property
    def _themes_root(self) -> Path:
        return Path(settings.MYLONITE_THEMES_ROOT)

    def _load_theme_context(self):
        resolver = ThemeResolver(self._themes_root)
        site_theme_settings = load_active_theme_settings(content_root=self._content_root)
        discovered_themes = resolver.discover_themes()
        resolved_theme = resolver.resolve(
            site_theme_settings,
            themes=discovered_themes,
        )
        selectable_themes = resolver.selectable_themes(
            custom_theme_allowed=site_theme_settings.custom_theme_allowed,
            themes=discovered_themes,
        )

        return {
            "site_theme_settings": site_theme_settings,
            "resolved_theme": resolved_theme,
            "selectable_themes": selectable_themes,
            "theme_choices": [
                (
                    theme.theme_id,
                    f"{theme.metadata.name} ({theme.theme_id})",
                )
                for theme in selectable_themes
            ],
        }

    def _get_password_form(self, data=None):
        return PanelPasswordChangeForm(self.request.user, data=data)

    def _get_theme_form(self, *, theme_choices, data=None, initial_theme_id="default"):
        return ThemeSelectionForm(
            data=data,
            theme_choices=theme_choices,
            initial={"theme_name": initial_theme_id},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        theme_context = self._load_theme_context()

        password_form = kwargs.get("password_form") or self._get_password_form()
        theme_form = kwargs.get("theme_form") or self._get_theme_form(
            theme_choices=theme_context["theme_choices"],
            initial_theme_id=theme_context["resolved_theme"].active_theme.theme_id,
        )

        context["password_form"] = password_form
        context["theme_form"] = theme_form
        context["theme_options"] = theme_context["selectable_themes"]
        context["active_theme_id"] = theme_context["resolved_theme"].active_theme.theme_id
        context["custom_theme_allowed"] = (
            theme_context["site_theme_settings"].custom_theme_allowed
        )
        context["missing_theme_files"] = (
            theme_context["resolved_theme"].missing_required_static_files
        )
        return context

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        action = request.POST.get("settings_action", "").strip().lower()
        if action == "password":
            return self._handle_password_update()
        if action == "theme":
            return self._handle_theme_update()
        return redirect("panel:settings")

    def _handle_password_update(self) -> HttpResponse:
        password_form = self._get_password_form(data=self.request.POST)
        theme_context = self._load_theme_context()
        theme_form = self._get_theme_form(
            theme_choices=theme_context["theme_choices"],
            initial_theme_id=theme_context["resolved_theme"].active_theme.theme_id,
        )

        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(self.request, user)
            messages.success(self.request, "Password updated successfully.")
            return redirect("panel:settings")

        context = self.get_context_data(
            password_form=password_form,
            theme_form=theme_form,
        )
        return self.render_to_response(context)

    def _handle_theme_update(self) -> HttpResponse:
        theme_context = self._load_theme_context()
        password_form = self._get_password_form()
        theme_form = self._get_theme_form(
            data=self.request.POST,
            theme_choices=theme_context["theme_choices"],
            initial_theme_id=theme_context["resolved_theme"].active_theme.theme_id,
        )

        if theme_form.is_valid():
            selected_theme_id = theme_form.cleaned_data["theme_name"]
            payload = load_site_config_payload(self._content_root)
            theme_payload = payload.setdefault("theme", {})
            theme_payload["name"] = selected_theme_id
            write_site_config_payload(self._content_root, payload)

            selected_theme = next(
                (
                    theme
                    for theme in theme_context["selectable_themes"]
                    if theme.theme_id == selected_theme_id
                ),
                None,
            )
            display_name = (
                selected_theme.metadata.name if selected_theme else selected_theme_id
            )
            messages.success(
                self.request,
                f"Theme updated to {display_name}.",
            )
            return redirect("panel:settings")

        context = self.get_context_data(
            password_form=password_form,
            theme_form=theme_form,
        )
        return self.render_to_response(context)
