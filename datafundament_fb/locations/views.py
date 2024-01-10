import csv
from django.shortcuts import render
from django.views.generic import View
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from django.urls import reverse
from django.utils import timezone
from locations.models import Location
from locations.processors import LocationDataProcessor

# Create your views here.
class LocationExportView(View):
    template = 'locations/location-export.html'

    def get(self, request, *args, **kwargs):
        return render(request=request, template_name=self.template)

    def post(self, request, *args, **kwargs):
        locations = Location.objects.all()
        location_data = []
        for location in locations:
            location_data.append(LocationDataProcessor.get(pandcode=location.pandcode).get_dict())

        date = timezone.now().strftime('%Y-%m-%d_%H.%M')
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename="locaties_export_{date}.csv"'},
        )

        writer = csv.DictWriter(response, fieldnames=location_data[0].keys())
        writer.writeheader()
        writer.writerows(location_data)

        return response