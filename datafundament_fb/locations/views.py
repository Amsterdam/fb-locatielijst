from django.views.generic import ListView, View
from django.shortcuts import render
from django.contrib import messages
from django.urls import reverse
from locations.models import Location, compute_pandcode
from locations.forms import LocationDetailForm
from locations.processors import LocationDataProcessor
from django.http import HttpResponseRedirect

# Create your views here.
class LocationListView(ListView):
    model = Location
    
    def get(self, request, *args, **kwargs):
        return super(LocationListView, self).get(request, *args, **kwargs)
    

class LocationDetailView(View):  
    form = LocationDetailForm
    template = 'locations/location-detail.html'

    def get(self, request, *args, **kwargs):
        initial_data = LocationDataProcessor.get(pandcode=self.kwargs['id']).get_dict()
        form = self.form(initial=initial_data)
        context = {'form': form, 'pandcode': self.kwargs['id'], 'location_data': initial_data}
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
            return HttpResponseRedirect(reverse('location-detail', args=[self.kwargs['id']]))

        context = {'form': form}
        return render(request, template_name=self.template, context=context)


class LocationUpdateView(View):
    form = LocationDetailForm
    template = 'locations/location-update.html'

    def get(self, request, *args, **kwargs):
        initial_data = LocationDataProcessor.get(pandcode=self.kwargs['id']).get_dict()
        form = self.form(initial=initial_data)
        context = {'form': form, 'pandcode': self.kwargs['id'], 'location_data': initial_data}
        return render(request=request, template_name=self.template, context=context)


    def post(self, request, *args, **kwargs):
        form = self.form(request.POST)
        # ALS ID IS GEGEVEN DAN IS HET EEN BESTAANDE LOCATIE???
        
        pandcode = self.kwargs['id'] if self.kwargs['id'] else compute_pandcode()
        if form.is_valid():
            # TODO {'pandcode': ['Locatie with this Pandcode already exists.'], 'name': ['Locatie with this Locatie already exists.']}
            # TOCH UPDATE/CREATE MAKEN IN LOCATIONDATAPROCESSOR.SAVE()??
            # OF FILTEREN OP NIEUW IN REQUEST BODY OID?
            if Location.objects.filter(pandcode=pandcode).exists():
                location_data = LocationDataProcessor.get(pandcode=pandcode)
                for field in location_data.location_properties:
                    if getattr(location_data, field) != form.cleaned_data[field]:
                        setattr(location_data, field, form.cleaned_data[field])
            else:
                location_data = LocationDataProcessor(form.cleaned_data)
            
            location_data.save()
            messages.success(request, 'De locatie is opgeslagen')
            return HttpResponseRedirect(reverse('location-detail', args=[self.kwargs['id']]))

        context = {'form': form, 'pandcode': pandcode}
        return render(request, template_name=self.template, context=context)