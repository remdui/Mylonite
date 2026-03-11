from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", include("apps.panel.urls")),
    path("django-admin/", admin.site.urls),
    path("", include("apps.web.urls")),
]
