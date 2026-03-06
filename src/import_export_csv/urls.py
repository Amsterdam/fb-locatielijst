from django.urls import path

from import_export_csv.views import LocatieImportView

urlpatterns = [
    path("import", view=LocatieImportView.as_view(), name="locatie-import"),
]
