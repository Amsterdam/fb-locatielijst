from django.urls import path

from import_export_csv.views import LocatieImportView, LocationExportView

urlpatterns = [
    path("import", view=LocatieImportView.as_view(), name="locatie-import"),
    path("export", view=LocationExportView.as_view(), name="locatie-export"),
]
