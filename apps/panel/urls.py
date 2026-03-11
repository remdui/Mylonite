from django.urls import path

from . import views

app_name = "panel"

urlpatterns = [
    path("", views.AdminRootView.as_view(), name="root"),
    path("setup/", views.SetupView.as_view(), name="setup"),
    path("setup/complete/", views.SetupCompleteView.as_view(), name="setup_complete"),
    path("login/", views.PanelLoginView.as_view(), name="login"),
    path("logout/", views.PanelLogoutView.as_view(), name="logout"),
    path("dashboard/", views.PanelDashboardView.as_view(), name="dashboard"),
    path("settings/", views.PanelSettingsView.as_view(), name="settings"),
]
