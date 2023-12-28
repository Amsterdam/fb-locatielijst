from django.views.generic import ListView, View
from django.shortcuts import render
from django.contrib import messages
from django.urls import reverse
from locations.models import Location, compute_building_code
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
        initial_data = LocationDataProcessor.get(building_code=self.kwargs['id']).get_dict()
        form = self.form(initial=initial_data)
        context = {'form': form, 'building_code': self.kwargs['id'], 'location_data': initial_data}
        return render(request=request, template_name=self.template, context=context)


    def post(self, request, *args, **kwargs):
        form = self.form(request.POST)
        # ALS ID IS GEGEVEN DAN IS HET EEN BESTAANDE LOCATIE???
        
        building_code = self.kwargs['id'] if self.kwargs['id'] else compute_building_code()
        if form.is_valid():
            # TODO {'building_code': ['Locatie with this Pandcode already exists.'], 'name': ['Locatie with this Locatie already exists.']}
            # TOCH UPDATE/CREATE MAKEN IN LOCATIONDATAPROCESSOR.SAVE()??
            # OF FILTEREN OP NIEUW IN REQUEST BODY OID?
            if Location.objects.filter(building_code=building_code).exists():
                location_data = LocationDataProcessor.get(building_code=building_code)
                for field in location_data.location_properties_list:
                    if getattr(location_data, field) != form.cleaned_data[field]:
                        setattr(location_data, field, form.cleaned_data[field])
            else:
                location_data = LocationDataProcessor(form.cleaned_data)
            
            location_data.save()
            messages.success(request, 'De locatie is opgeslagen')
            return HttpResponseRedirect(reverse('location-detail', args=[self.kwargs['id']]))

        context = {'form': form, 'building_code': building_code}
        return render(request, template_name=self.template, context=context)

def location_view_edit(request, id):
    if request.method == 'GET':
        context = {
            'location_data': LocationDataProcessor.get(building_code=id).get_dict()
        }
        
        return render(request, template_name='locations/location_edit.html', context=context)

    if request.method == 'POST':
        form_data = dict(request.POST)
        location = LocationDataProcessor.get(building_code=id)
        location.name = form_data['name'][0]
        setattr(location, 'Adres validatie', form_data['Adres validatie'][0])
        location.save()

        messages.success(request, 'De locatie is opgeslagen')
        return HttpResponseRedirect(reverse('location-detail', args=[id]))


class LocationCreateView():...


class LocationUpdateView():...