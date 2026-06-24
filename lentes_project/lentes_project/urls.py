from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView


urlpatterns = [
    path("", RedirectView.as_view(pattern_name="lentes:dashboard", permanent=False)),
    path("admin/", admin.site.urls),
    path("lentes/", include("apps.lentes.urls")),
]
