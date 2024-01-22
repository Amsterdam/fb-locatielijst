import csv
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
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
def home_page(request):
    return HttpResponseRedirect(reverse('location-list'))

class LocationListView(ListView):
    model = Location
    template_name = 'locations/location-list.html'
    
    def get(self, request, *args, **kwargs):
        return super(LocationListView, self).get(request, *args, **kwargs)
    

class LocationDetailView(View):  
    form = LocationDataForm
    template = 'locations/location-detail.html'

    def get(self, request, *args, **kwargs):
        # Return all location properties when a user is logged in
        if request.user.is_authenticated:
            location_data = LocationProcessor.get(pandcode=self.kwargs['id'], private=True)
            form = self.form(initial=location_data.get_dict(), private=True)
        else:
            location_data = LocationProcessor.get(pandcode=self.kwargs['id'])
            form = self.form(initial=location_data.get_dict())
        context = {'form': form, 'location_data': location_data.get_dict()}
        return render(request=request, template_name=self.template, context=context)


class LocationCreateView(LoginRequiredMixin, View):
    form = LocationDataForm
    template = 'locations/location-create.html'
    
    def get(self, request, *args, **kwargs):
        form = self.form(private=True)
        context = {'form': form}
        return render(request=request, template_name=self.template, context=context)

    def post(self, request, *args, **kwargs):
        form = self.form(request.POST, private=True)

        if form.is_valid():
            location_data = LocationProcessor(form.cleaned_data, private=True)
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


class LocationUpdateView(LoginRequiredMixin, View):
    form = LocationDataForm
    template = 'locations/location-update.html'

    def get(self, request, *args, **kwargs):
        location_data = LocationProcessor.get(pandcode=self.kwargs['id'], private=True)
        form = self.form(initial=location_data.get_dict(), private=True)
        context = {'form': form, 'location_data': location_data.get_dict()}
        return render(request=request, template_name=self.template, context=context)

    def post(self, request, *args, **kwargs):
        form = self.form(request.POST, private=True)
        location_data = LocationProcessor.get(pandcode=self.kwargs['id'], private=True)

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


class LocationImportView(LoginRequiredMixin, View):
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
                location_properties = set(LocationProcessor(private=True).location_properties)
                headers = set(csv_dict.fieldnames)

                used_columns = list(headers & location_properties)
                message = f"Kolommen {used_columns} worden verwerkt"
                messages.add_message(request, messages.INFO, message)

                # Process the rows from the import file
                for row in csv_dict:
                    # Initiatie a location processor with the row data
                    location = LocationProcessor(data=row, private=True)
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
            # Return all location properties when a user is logged in
            if request.user.is_authenticated:
                location_data.append(LocationProcessor.get(pandcode=location.pandcode, private=True).get_dict())
            else:
                location_data.append(LocationProcessor.get(pandcode=location.pandcode).get_dict())

        # Setup the http response with the 
        date = timezone.localtime(timezone.now()).strftime('%Y-%m-%d_%H.%M')
        response = HttpResponse(
            content_type='text/csv, charset=utf-8',
            headers={'Content-Disposition': f'attachment; filename="locaties_export_{date}.csv"'},
        )

        # Add BOM to the file; because otherwise Excel won't know what's happening
        response.write('\ufeff'.encode('utf-8'))

        # Setup a csv dictwriter and write the location data to the response object
        headers = location_data[0].keys()
        writer = csv.DictWriter(response, fieldnames=headers)
        writer.writeheader()
        writer.writerows(location_data)

        # Return the response
        return response


class LocationAdminView(LoginRequiredMixin, View):
    template = 'locations/location-beheer.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, template_name=self.template)

