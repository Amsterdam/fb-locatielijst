from django.urls import path

from fblocatie.views import (
    LocatieListView,
)

urlpatterns = [
    path("", view=LocatieListView.as_view(), name="locatie-list"),
]
