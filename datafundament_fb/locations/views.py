from django.views.generic import ListView, View
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.urls import reverse
from locations.forms import LocationDetailForm
from locations.models import Location
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
            for field in form.cleaned_data:
                    setattr(location_data, field, form.cleaned_data[field])
            
            location_data.save()
            messages.success(request, 'De locatie is opgeslagen')
            return HttpResponseRedirect(reverse('location-detail', args=[self.kwargs['id']]))
        else:
            context = {'form': form, 'location_data': location_data.get_dict()}
            return render(request, template_name=self.template, context=context)