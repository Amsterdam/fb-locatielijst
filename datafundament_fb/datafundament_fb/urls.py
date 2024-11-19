"""
URL configuration for datafundament_fb project.

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
from django.urls import include, path
from .settings.auth import oidc_login, oidc_logout
from locations.views import (home_page,)

# Local development and tests uses default Django authentication backend 
if environ.get('ENVIRONMENT') == 'local':
    urlpatterns = [
        path('auth/login', LoginView.as_view(template_name='login.html'), name='login'),
        path('auth/logout', LogoutView.as_view(), name='logout'),
    ]
else:
    urlpatterns = [
        path('oidc/', include("mozilla_django_oidc.urls")),
        # This will, purposefully, never hit, but will provide a reverse lookup for the logout/login url
        path('oidc/login', oidc_login, name='login'),
        path('oidc/logout/', oidc_logout, name='logout'),
    ]

urlpatterns.extend([
    path('admin/', admin.site.urls),
    path('locaties/', include(('locations.urls', 'locations'), namespace='locations_urls')),
    path('health/', include(('health.urls', 'health'), namespace='health_urls')),
    path('help/', include(('help_docs.urls', 'help_docs'), namespace='help_docs_urls')),
    path('', home_page, name='home'),
])