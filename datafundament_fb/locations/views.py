from django.views.generic import ListView, View
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.urls import reverse
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
            location_data.save()

            messages.success(request, 'De locatie is toegevoegd')
            return HttpResponseRedirect(reverse('location-detail', args=[location_data.pandcode]))
        else:
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
            location_data.save()

            messages.success(request, 'De locatie is opgeslagen')
            return HttpResponseRedirect(reverse('location-detail', args=[location_data.pandcode]))
        else:
            context = {'form': form, 'location_data': location_data.get_dict()}
            return render(request, template_name=self.template, context=context)


class LocationBeheerView(View):
    template = 'locations/location-beheer.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, template_name=self.template)