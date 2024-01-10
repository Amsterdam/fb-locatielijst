from django.urls import path
from locations.views import LocationImportView

urlpatterns = [
    path('import', LocationImportView.as_view(), name='location-import'),
]