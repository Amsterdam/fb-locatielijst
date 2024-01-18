from django.urls import path
from locations.views import LocationListView, LocationDetailView, LocationCreateView, LocationUpdateView

urlpatterns = [
    path('', view=LocationListView.as_view(), name='location-list'),
    path('new', view=LocationCreateView.as_view(), name='location-create'),
    path('<int:id>', view=LocationDetailView.as_view(), name='location-detail'),
    path('<int:id>/edit', view=LocationUpdateView.as_view(), name='location-update'),
]