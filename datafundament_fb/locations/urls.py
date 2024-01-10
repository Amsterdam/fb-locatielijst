from django.urls import path
from locations.views import LocationExportView

urlpatterns = [
    path('export', view=LocationExportView.as_view(), name='location-export'),
]