# TODO Excel exporteert standaard niet met quoted velden en is komma gescheiden!!!! Wat o wat te doen? Import xslx?
import csv
from django.views.generic import ListView, View
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.urls import reverse
from locations.forms import ImportCsvForm, LocationDetailForm
from locations.models import Location, compute_pandcode
from locations.processors import LocationDataProcessor

# Create your views here.
class LocationListView(ListView):
    model = Location
    template_name = 'locations/location-list.html'
    
    def get(self, request, *args, **kwargs):
        return super(LocationListView, self).get(request, *args, **kwargs)
    

class LocationDetailView(View):  
    form = LocationDetailForm
    template = 'locations/location-detail.html'

    def get(self, request, *args, **kwargs):
        location_data = LocationDataProcessor.get(pandcode=self.kwargs['id'])
        initial_data = location_data.get_dict()
        form = self.form(initial=initial_data)
        context = {'form': form, 'location_data': initial_data, 'gewijzigd': location_data.gewijzigd}
        return render(request=request, template_name=self.template, context=context)


class LocationCreateView(View):
    form = LocationDetailForm
    template = 'locations/location-create.html'
    
    def get(self, request, *args, **kwargs):
        form = self.form()
        context = {'form': form}
        return render(request=request, template_name=self.template, context=context)

    def post(self, request, *args, **kwargs):
        form = self.form(request.POST)
        # ALS ID IS GEGEVEN DAN IS HET EEN BESTAANDE LOCATIE???
        
        if form.is_valid():
            location_data = LocationDataProcessor(form.cleaned_data)
            location_data.save()
            messages.success(request, 'De locatie is opgeslagen')
            return HttpResponseRedirect(reverse('location-detail', args=[location_data.pandcode]))

        context = {'form': form}
        return render(request, template_name=self.template, context=context)


class LocationUpdateView(View):
    form = LocationDetailForm
    template = 'locations/location-update.html'

    def get(self, request, *args, **kwargs):
        initial_data = LocationDataProcessor.get(pandcode=self.kwargs['id']).get_dict()
        form = self.form(initial=initial_data)
        context = {'form': form, 'location_data': initial_data, 'pandcode': self.kwargs['id']}
        return render(request=request, template_name=self.template, context=context)


    def post(self, request, *args, **kwargs):
        form = self.form(request.POST)
        location_data = LocationDataProcessor.get(pandcode=self.kwargs['id'])

        if form.is_valid():
            # ALS ID IS GEGEVEN DAN IS HET EEN BESTAANDE LOCATIE???
            for field in form.cleaned_data:
                    setattr(location_data, field, form.cleaned_data[field])
            
            location_data.save()
            messages.success(request, 'De locatie is opgeslagen')
            return HttpResponseRedirect(reverse('location-detail', args=[self.kwargs['id']]))
        else:
            context = {'form': form, 'location_data': location_data.get_dict()}
            return render(request, template_name=self.template, context=context)
    
    
class ImportCsvView(View):

    def get(self, request):
        # render the form
        form = ImportCsvForm()
        # set context for the rederer
        context = {'form': form}
        
        return render(request, template_name='locations/import_csv.html', context=context)

    def post(self, request):
        # handle the form post
        form = ImportCsvForm(request.POST, request.FILES)
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
                    # TODO iets doen met last_modified kolom, die moet niet autonow hebben om dit te kunnen importeren
                    messages.add_message(
                        request,
                        messages.ERROR,
                        'De volgende kolom mist in de csv: {column}'.format(column=property)
                    )
                    column_not_in_csv = True
            
            for column in headers:
                if column not in location_properties:
                    messages.add_message(
                        request,
                        messages.ERROR,
                        'De volgende kolom in de csv wordt niet verwerkt: {column}'.format(column=column)
                    )
                    column_not_in_properties = True

            if column_not_in_csv or column_not_in_properties:    
                return HttpResponseRedirect(reverse('import-csv'))

            # get all location properties choices
            # location_property_choices = LocationProperty.objects.filter(property_type='CHOICE')
            # location_properties_choice_list = [obj.name for obj in location_property_choices]

            for row in csv_dict:
                # TODO get_or_create functie maken voor LocationDataProcessor? Als een object gevuld wordt met een dict, hoe te controleren of deze al bestaat en geupdate moet worden
                # if Location.objects.filter(pandcode=row['pandcode']).exists():
                #     LocationDataProcessor.get(pandcode=row['pandcode'])

                # DIT ZOU OOK NAAR DE PROCESSOR KUNNEN; WANNEER ER EEN NIET BESTAANDE CHOICE WORDT OPGEGEVEN WORDT DEZE METEEN IN DE DB GEZET
                # for location_property in row.items:
                #     if location_property in location_properties_choice_list:
                #         if location

                try:
                    # Controleren of het object al bestaat; en dan dus ook een update functie in de processor definiëren
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
        
        return HttpResponseRedirect(reverse('import-csv'))