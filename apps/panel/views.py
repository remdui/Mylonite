from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import FormView, TemplateView

from .forms import OwnerSetupForm, PanelAuthenticationForm, PanelPasswordChangeForm
from .models import SiteSetup
from .services import (
    InitialSetupAlreadyComplete,
    get_setup_state,
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
            raise PermissionDenied("You do not have access to this administrative panel.")

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
                    setup.completed_at = transaction.get_connection().ops.adapt_datetimefield_value
                    setup.completed_at = None
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

        setup = SiteSetup.get_solo()
        if setup.completed_at is None:
            from django.utils import timezone

            setup.completed_at = timezone.now()
            setup.save(update_fields=["completed_at", "updated_at"])

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
        "This administrative panel is ready for future editors, validation tools, "
        "and content management features."
    )


class PanelSettingsView(
    OwnerRequiredMixin,
    PanelContextMixin,
    auth_views.PasswordChangeView,
):
    template_name = "panel/settings.html"
    form_class = PanelPasswordChangeForm
    success_url = reverse_lazy("panel:settings")
    panel_section = "settings"
    panel_heading = "Settings"
    panel_description = "Update your owner account credentials."

    def form_valid(self, form):
        messages.success(self.request, "Password updated successfully.")
        return super().form_valid(form)
