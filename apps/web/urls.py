from django.urls import path

from . import views

urlpatterns = [
    path("theme-static/<path:asset_path>", views.theme_static, name="theme_static"),
    path("health/", views.health, name="health"),
    path("", views.home, name="home"),
]
