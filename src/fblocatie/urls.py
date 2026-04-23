from django.urls import path

from fblocatie.views import (
    LocatieDetailView,
    LocatieListView,
)

urlpatterns = [
    path("", view=LocatieListView.as_view(), name="locatie-list"),
    path("<int:pandcode>", view=LocatieDetailView.as_view(), name="locatie-detail"),
]
