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
from locations.processors import LocationProcessor

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
            if csv_file.name.endswith('.csv'):
                csv_reader = csv_file.read().decode('utf-8-sig').splitlines()
                csv_dict = csv.DictReader(csv_reader)

                # Report columns that will be processed during import
                location_properties = set(LocationProcessor().location_properties)
                headers = set(csv_dict.fieldnames)

                used_columns = list(headers & location_properties)
                message = f"Kolommen {used_columns} worden verwerkt"
                messages.add_message(request, messages.INFO, message)

                # Process the rows from the import file
                for row in csv_dict:
                    # Initiatie a location processor with the row data
                    location = LocationProcessor(row)
                    try:
                        # Save the locationprocessor instance                        
                        location.save()

                        # Return message for success
                        message = f"Locatie {row['naam']} is geïmporteerd/ge-update"
                        messages.add_message(request, messages.SUCCESS, message)

                    except ValidationError as err:
                        message = f"Fout bij het importeren voor locatie {row['naam']}: {err.message}"
                        messages.add_message(request, messages.ERROR, message)
            else:
                message = f"{csv_file.name} is geen gelding CSV bestand"
                messages.add_message(request, messages.ERROR, message)
        else:
            message = f"Something went wrong validating your input: {form.errors}"
            messages.add_message(request, messages.ERROR, message)
        
        return HttpResponseRedirect(reverse('location-import'))