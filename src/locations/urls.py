from django.urls import path

from locations.views import (
    ExternalServiceCreateView,
    ExternalServiceDeleteView,
    ExternalServiceUpdateView,
    ExternalServivceListView,
    LocationAdminView,
    LocationCreateView,
    LocationDetailView,
    LocationExportView,
    LocationImportView,
    LocationListView,
    LocationLogView,
    LocationPropertyCreateView,
    LocationPropertyDeleteView,
    LocationPropertyListView,
    LocationPropertyUpdateView,
    LocationUpdateView,
    PropertyGroupCreateView,
    PropertyGroupDeleteView,
    PropertyGroupListView,
    PropertyGroupUpdateView,
    PropertyOptionCreateView,
    PropertyOptionDeleteView,
    PropertyOptionListView,
    PropertyOptionUpdateView,
)

urlpatterns = [
    path("", view=LocationListView.as_view(), name="location-list"),
    path("<int:pandcode>", view=LocationDetailView.as_view(), name="location-detail"),
    path("<int:pandcode>/wijzigen", view=LocationUpdateView.as_view(), name="location-update"),
    path("toevoegen", view=LocationCreateView.as_view(), name="location-create"),
    path("beheer", view=LocationAdminView.as_view(), name="location-admin"),
    path("export", view=LocationExportView.as_view(), name="location-export"),
    path("import", LocationImportView.as_view(), name="location-import"),
    path("log/", view=LocationLogView.as_view(), name="location-log"),
    path("log/locatie/<int:pandcode>", view=LocationLogView.as_view(), name="location-detail-log"),
    path("locatie-eigenschappen/", view=LocationPropertyListView.as_view(), name="locationproperty-list"),
    path("locatie-eigenschappen/toevoegen", view=LocationPropertyCreateView.as_view(), name="locationproperty-create"),
    path(
        "locatie-eigenschappen/<int:pk>/wijzigen",
        view=LocationPropertyUpdateView.as_view(),
        name="locationproperty-update",
    ),
    path(
        "locatie-eigenschappen/<int:pk>/verwijderen",
        view=LocationPropertyDeleteView.as_view(),
        name="locationproperty-delete",
    ),
    path(
        "locatie-eigenschappen/<int:lp_pk>/opties/", view=PropertyOptionListView.as_view(), name="propertyoption-list"
    ),
    path(
        "locatie-eigenschappen/<int:lp_pk>/opties/aanmaken",
        view=PropertyOptionCreateView.as_view(),
        name="propertyoption-create",
    ),
    path(
        "locatie-eigenschappen/<int:lp_pk>/opties/<int:pk>/wijzigen",
        view=PropertyOptionUpdateView.as_view(),
        name="propertyoption-update",
    ),
    path(
        "locatie-eigenschappen/<int:lp_pk>/opties/<int:pk>/verwijderen",
        view=PropertyOptionDeleteView.as_view(),
        name="propertyoption-delete",
    ),
    path("eigenschap-groepen/", view=PropertyGroupListView.as_view(), name="propertygroup-list"),
    path("eigenschap-groepen/aanmaken", view=PropertyGroupCreateView.as_view(), name="propertygroup-create"),
    path("eigenschap-groepen/<int:pk>/wijzigen", view=PropertyGroupUpdateView.as_view(), name="propertygroup-update"),
    path(
        "eigenschap-groepen/<int:pk>/verwijderen", view=PropertyGroupDeleteView.as_view(), name="propertygroup-delete"
    ),
    path("externe-koppelingen/", view=ExternalServivceListView.as_view(), name="externalservice-list"),
    path("externe-koppelingen/aanmaken", view=ExternalServiceCreateView.as_view(), name="externalservice-create"),
    path(
        "externe-koppelingen/<int:pk>/wijzigen", view=ExternalServiceUpdateView.as_view(), name="externalservice-update"
    ),
    path(
        "externe-koppelingen/<int:pk>/verwijderen",
        view=ExternalServiceDeleteView.as_view(),
        name="externalservice-delete",
    ),
]
