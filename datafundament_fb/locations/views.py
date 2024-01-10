# TODO Excel exporteert standaard niet met quoted velden en is komma gescheiden!!!! Wat o wat te doen? Import xslx?
import csv
from django.views.generic import View
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.urls import reverse
from locations.forms import LocationImportForm
from locations.models import Location
from locations.processors import LocationDataProcessor

# Create your views here.
class LocationImportView(View):
    form = LocationImportForm
    template_name = 'locations/location-import.html'

    def get(self, request):
        form = self.form()
        context = {'form': form}
        
        return render(request, template_name=self.template_name, context=context)

    def post(self, request):
        form = self.form(request.POST, request.FILES)

        if form.is_valid():
            csv_file = form.cleaned_data.get('csv_file')
            csv_reader = csv_file.read().decode('utf-8-sig').splitlines()
            csv_dict = csv.DictReader(csv_reader)

            # verify column header names against location_data properties
            location_properties = LocationDataProcessor().location_properties
            column_not_in_csv = False
            column_not_in_properties = False
            headers = csv_dict.fieldnames

            for property in location_properties:
                if property not in headers:
                    messages.add_message(
                        request,
                        messages.WARNING,
                        'De volgende eigenshaip mist in het import bestand: {column}'.format(column=property)
                    )
            
            for column in headers:
                if column not in location_properties:
                    messages.add_message(
                        request,
                        messages.WARNING,
                        'De volgende kolom in het import bestand bestaat niet als eigenschap: {column}'.format(column=column)
                    )

            for row in csv_dict:
                try:
                    if Location.objects.filter(pandcode=row['pandcode']).exists():
                        message = 'Locatie {name} is ge-update'.format(name=row['naam'])
                    else:
                        message = 'Locatie {name} is geïmporteerd'.format(name=row['naam'])
                    
                    location = LocationDataProcessor(row)
                    location.save()
                    messages.add_message(
                        request,
                        messages.INFO, message
                    )
                except ValidationError as err:
                    messages.add_message(
                        request,
                        messages.ERROR, 'Fout bij het importeren voor locatie {name}: {message}'.format(
                            name=row['naam'],
                            message=err.messages
                        )
                    )       
        else:
            messages.add_message(request, messages.ERROR, 'Something went wrong validating your input: {errors}.'.format(errors = form.errors))
        
        return HttpResponseRedirect(reverse('location-import'))