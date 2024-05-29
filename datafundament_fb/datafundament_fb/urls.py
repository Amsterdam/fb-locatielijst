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
from django.contrib import admin
from django.urls import include, path
from locations.views import (
    home_page, LocationAdminView, LocationLogView, 
    LocationPropertyListView, LocationPropertyCreateView, LocationPropertyUpdateView, LocationPropertyDeleteView,
    PropertyOptionListView, PropertyOptionCreateView, PropertyOptionUpdateView, PropertyOptionDeleteView,
    PropertyGroupListView, PropertyGroupCreateView, PropertyGroupUpdateView, PropertyGroupDeleteView,
    ExternalServivceListView, ExternalServiceCreateView, ExternalServiceUpdateView, ExternalServiceDeleteView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('locaties/', include(('locations.urls', 'locations'), namespace='locations_urls')),
    path('help/', include(('help_docs.urls', 'help_docs'), namespace='help_docs_urls')),
    path('', home_page, name='home'),
]