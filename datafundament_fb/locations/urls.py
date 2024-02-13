from django.urls import path
from locations.views import LocationListView, LocationDetailView, LocationCreateView, LocationUpdateView, LocationImportView, LocationExportView

urlpatterns = [
    path('', view=LocationListView.as_view(), name='location-list'),
    path('new', view=LocationCreateView.as_view(), name='location-create'),
    path('<int:pandcode>', view=LocationDetailView.as_view(), name='location-detail'),
    path('<int:pandcode>/edit', view=LocationUpdateView.as_view(), name='location-update'),
    path('import', LocationImportView.as_view(), name='location-import'),
    path('export', view=LocationExportView.as_view(), name='location-export'),
]