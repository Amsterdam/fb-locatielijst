import csv
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic import View, ListView
from django.urls import reverse
from django.utils import timezone
from locations.forms import LocationDataForm, LocationImportForm
from locations.models import Location
from locations.processors import LocationProcessor

# Create your views here.
class LocationListView(ListView):
    model = Location
    template_name = 'locations/location-list.html'
    
    def get(self, request, *args, **kwargs):
        return super(LocationListView, self).get(request, *args, **kwargs)
    

class LocationDetailView(View):  
    form = LocationDataForm
    template = 'locations/location-detail.html'

    def get(self, request, *args, **kwargs):
        location_data = LocationProcessor.get(pandcode=self.kwargs['id'])
        form = self.form(initial=location_data.get_dict())
        context = {'form': form, 'location_data': location_data.get_dict()}
        return render(request=request, template_name=self.template, context=context)


class LocationCreateView(View):
    form = LocationDataForm
    template = 'locations/location-create.html'
    
    def get(self, request, *args, **kwargs):
        form = self.form()
        context = {'form': form}
        return render(request=request, template_name=self.template, context=context)

    def post(self, request, *args, **kwargs):
        form = self.form(request.POST)

        if form.is_valid():
            location_data = LocationProcessor(form.cleaned_data)
            try:
                # Save the locationprocessor instance
                location_data.save()
                messages.success(request, 'De locatie is toegevoegd')

            except ValidationError as err:
                # Return error message when the location is not saved
                # TODO: err message is not pretty, could be better
                message = f"Fout bij het aanmaken van de locatie: {err}"
                messages.error(request, message)
                context = {'form': form}
                
                return render(request, template_name=self.template, context=context)

            return HttpResponseRedirect(reverse('location-detail', args=[location_data.pandcode]))

        message = f"Niet alle velden zijn juist ingevuld"
        messages.error(request,message)
        context = {'form': form}
        return render(request, template_name=self.template, context=context)


class LocationUpdateView(View):
    form = LocationDataForm
    template = 'locations/location-update.html'

    def get(self, request, *args, **kwargs):
        location_data = LocationProcessor.get(pandcode=self.kwargs['id'])
        form = self.form(initial=location_data.get_dict())
        context = {'form': form, 'location_data': location_data.get_dict()}
        return render(request=request, template_name=self.template, context=context)


    def post(self, request, *args, **kwargs):
        form = self.form(request.POST)
        location_data = LocationProcessor.get(pandcode=self.kwargs['id'])

        if form.is_valid():
            for field in form.cleaned_data:
                setattr(location_data, field, form.cleaned_data[field])
            
            try:
                # Save the locationprocessor instance
                location_data.save()
                messages.success(request, 'De locatie is opgeslagen')
            
            except ValidationError as err:
                # Return error message when the location is not saved
                # TODO: err message is not pretty, could be better
                message = f"Fout bij het updaten van de locatie: {err}"
                messages.error(request, message)
                context = {'form': form, 'location_data': location_data.get_dict()}
                
                return render(request, template_name=self.template, context=context)

            return HttpResponseRedirect(reverse('location-detail', args=[location_data.pandcode]))           

        message = f"Niet alle velden zijn juist ingevuld"
        messages.error(request, message)
        context = {'form': form, 'location_data': location_data.get_dict()}
        return render(request, template_name=self.template, context=context)


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
    

class LocationExportView(View):
    template = 'locations/location-export.html'

    def get(self, request, *args, **kwargs):
        return render(request=request, template_name=self.template)

    def post(self, request, *args, **kwargs):
        # Get all Location instances()
        locations = Location.objects.all()

        # Set all location data to a LocationProcessor
        location_data = []
        for location in locations:
            location_data.append(LocationProcessor.get(pandcode=location.pandcode).get_dict())

        # Setup the http response with the 
        date = timezone.now().strftime('%Y-%m-%d_%H.%M')
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename="locaties_export_{date}.csv"'},
        )

        # Setup a csv dictwriter and write the location data to the response object
        headers = location_data[0].keys()
        writer = csv.DictWriter(response, fieldnames=headers)
        writer.writeheader()
        writer.writerows(location_data)

        # Return the response
        return response