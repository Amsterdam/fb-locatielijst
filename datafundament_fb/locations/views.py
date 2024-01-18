import csv
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from django.views.generic import ListView
from locations.forms import LocationDataForm
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

