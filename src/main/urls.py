"""
URL configuration for FB Locatielijst project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from os import environ

from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponseRedirect
from django.urls import include, path, reverse
from django.views.generic import TemplateView, View

from main.view_403 import permissiondenied403


class AdminLogin(View):
    def get(self, request, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect(
                reverse("oidc_authentication_init") + (f"?next={request.GET.get('next', '/admin/')}")
            )

        if not request.user.is_staff:
            return HttpResponseRedirect("/403/")

        return HttpResponseRedirect(reverse("admin:index"))


# Local development and tests uses default Django authentication backend
if environ.get("ENVIRONMENT") == "local":
    urlpatterns = [
        path("auth/login", LoginView.as_view(template_name="login.html"), name="login"),
        path("auth/logout", LogoutView.as_view(), name="logout"),
    ]
else:
    urlpatterns = [path("oidc/", include("mozilla_django_oidc.urls")), path("admin/login/", AdminLogin.as_view())]

urlpatterns.extend(
    [
        path("admin/", admin.site.urls),
        path("locaties/", include(("locations.urls", "locations"), namespace="locations_urls")),
        path("health/", include("health.urls")),
        path("403/", permissiondenied403),
        path("help/", include(("help_docs.urls", "help_docs"), namespace="help_docs_urls")),
        path("", TemplateView.as_view(template_name="home.html"), name="home"),
    ]
)
