import csv
import urllib.parse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic import View, ListView
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from locations.forms import LocationDataForm, LocationImportForm, LocationListForm
from locations.models import Location, Log
from locations.processors import LocationProcessor

# Create your views here.
def home_page(request):
    return HttpResponseRedirect(reverse('locations_urls:location-list'))

def get_csv_file_response(request, locations)-> HttpResponse:
    """
    Method for returning a csv file within an http response object.
    Takes a list of Location objects as it input
    """
    # Set all location data to a LocationProcessor
    location_data = []
    for location in locations:
        # Get loction data  depending on user context; user == True is all location properties
        data = LocationProcessor.get(pandcode=location.pandcode, user=request.user).get_dict()
        # List values will be joined by the pipe '|' character instead of the default comma ','
        export_dict = dict()
        for key,value in data.items():
            if type(value) == list:
                export_dict[key] = '|'.join(value)
            else:
                export_dict[key] = value
        location_data.append(export_dict)

    # Setup the http response with the 
    date = timezone.localtime(timezone.now()).strftime('%Y-%m-%d_%H.%M')
    response = HttpResponse(
        content_type='text/csv, charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="locaties_export_{date}.csv"'},
    )

    # Add BOM to the file; because otherwise Excel won't know what's happening
    response.write('\ufeff'.encode('utf-8'))

    # Based on Locations presently in the database return the headers for the CSV file
    if location_data:
        headers = location_data[0].keys()
    else:
        headers = LocationProcessor(user=request.user).location_properties

    # Setup a csv dictwriter and write the location data to the response object
    writer = csv.DictWriter(response, fieldnames=headers, delimiter=';')
    writer.writeheader()
    writer.writerows(location_data)

    return response


class LocationListView(ListView):
    model = Location
    template_name = 'locations/location-list.html'
    paginate_by = 50

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.location_properties = LocationProcessor(user=request.user).location_property_instances

    def get_queryset(self):
        # Get a QuerySet of filtered and ordered locations
        order_by = self.request.GET.get('order_by')
        order = '-' if self.request.GET.get('order') == 'desc' else ''
        if not order_by in self.location_properties:
            order_by = 'pandcode'
        ordering = order + order_by

        # Get filtered and objects and annotated column
        locations = Location.objects.search_filter(
            params=self.request.GET.dict(),
            user=self.request.user).order_by(ordering)
        return locations

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        initial_data = self.request.GET
        # Render the search form
        context['form'] = LocationListForm(initial=initial_data, user=self.request.user)
        # Create at list of search input elements to be used in a JS function for hiding/unhiding these elements
        property_list = ['id_search']
        location_properties = LocationProcessor(user=self.request.user).location_property_instances
        for location_property in location_properties:
            if location_property.property_type == 'CHOICE':
                property_list.append('id_' + location_property.short_name)
        context['property_list'] = property_list
        # Number of locations in the search result, filtered by archive
        archive = self.request.GET.get('archive', '')
        location_count = Location.objects.archive_filter(archive).count()       
        context['location_count'] = location_count
        # Boolean if the search result if filtered by the search query
        context['is_filtered_result'] = context['page_obj'].paginator.count < location_count
        context['filtered_property'] = self.request.GET.get('property')
        return context
        

class LocationDetailView(View):  
    form = LocationDataForm
    template = 'locations/location-detail.html'

    def get(self, request, *args, **kwargs):
        # Get loction data  depending on user context; user == True is all location properties
        location_data = LocationProcessor.get(pandcode=self.kwargs['pandcode'], user=request.user)
        form = self.form(initial=location_data.get_dict(), user=request.user)
        context = {'form': form, 'location_data': location_data.get_dict()}
        return render(request=request, template_name=self.template, context=context)
    
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        pandcode = self.kwargs['pandcode']
        
        # Set is_archived based on _archive value
        location = Location.objects.get(pandcode=pandcode)
        if request.POST['_archive'] == 'archive':
            location.is_archived = True
        if request.POST['_archive'] == 'dearchive':
            location.is_archived = False
        location.save()
        
        # return to the location-detail page
        return HttpResponseRedirect(reverse('locations_urls:location-detail', args=[pandcode]))

class LocationCreateView(LoginRequiredMixin, View):
    form = LocationDataForm
    template = 'locations/location-create.html'
    
    def get(self, request, *args, **kwargs):
        form = self.form(user=request.user)
        context = {'form': form}
        return render(request=request, template_name=self.template, context=context)

    def post(self, request, *args, **kwargs):
        form = self.form(request.POST, user=request.user)

        if form.is_valid():
            location_data = LocationProcessor(data=form.cleaned_data, user=request.user)
            try:
                # Save the locationprocessor instance
                location_data.save()
                messages.success(request, 'De locatie is toegevoegd.')

            except ValidationError as err:
                # Return error message when the location is not saved
                message = f"Fout bij het aanmaken van de locatie: {err}."
                messages.error(request, message)
                context = {'form': form}
                
                return render(request, template_name=self.template, context=context)

            return HttpResponseRedirect(reverse('locations_urls:location-detail', args=[location_data.pandcode]))

        message = f"Niet alle velden zijn juist ingevuld."
        messages.error(request,message)
        context = {'form': form}
        return render(request, template_name=self.template, context=context)


class LocationUpdateView(LoginRequiredMixin, View):
    form = LocationDataForm
    template = 'locations/location-update.html'

    def get(self, request, *args, **kwargs):
        location_data = LocationProcessor.get(pandcode=self.kwargs['pandcode'], user=request.user)
        form = self.form(initial=location_data.get_dict(), user=request.user)
        context = {'form': form, 'location_data': location_data.get_dict()}
        return render(request=request, template_name=self.template, context=context)

    def post(self, request, *args, **kwargs):
        form = self.form(request.POST, pandcode=self.kwargs['pandcode'], user=request.user)
        # Get loction data  depending on user context; user == True is all location properties
        location_data = LocationProcessor.get(pandcode=self.kwargs['pandcode'], user=request.user)

        if form.is_valid():
            for field in form.cleaned_data:
                setattr(location_data, field, form.cleaned_data[field])
            
            try:
                # Save the locationprocessor instance
                location_data.save()
                messages.success(request, 'De locatie is opgeslagen.')
            
            except ValidationError as err:
                # Return error message when the location is not saved
                message = f"Fout bij het updaten van de locatie: {err}."
                messages.error(request, message)
                context = {'form': form, 'location_data': location_data.get_dict()}
                
                return render(request, template_name=self.template, context=context)

            return HttpResponseRedirect(reverse('locations_urls:location-detail', args=[location_data.pandcode]))

        message = f"Niet alle velden zijn juist ingevuld."
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
                try:
                    # Read the file as an utf-8 file
                    csv_reader = csv_file.read().decode('utf-8-sig').splitlines()
                    # Set the correct format for the csv by 'sniffing' the first line of the csv data and setting the delimiter
                    csv_dialect = csv.Sniffer().sniff(sample=csv_reader[0], delimiters=';')
                except:
                    message = "De locaties kunnen niet ingelezen worden. Zorg ervoor dat je ';' als scheidingsteken en UTF-8 als codering gebruikt."
                    messages.add_message(request, messages.ERROR, message)
                    
                    return HttpResponseRedirect(reverse('locations_urls:location-import'))

                csv_dict = csv.DictReader(csv_reader, dialect=csv_dialect, restval='missing', restkey='excess')

                # Report columns that will be processed during import
                location_properties = set(LocationProcessor(user=request.user).location_properties)
                headers = set(csv_dict.fieldnames)

                used_columns = list(headers & location_properties)
                message = f"Kolommen {used_columns} worden verwerkt."
                messages.add_message(request, messages.INFO, message)

                # Process the rows from the import file
                for i, row in enumerate(csv_dict):
                    # Check if a row is missing a value/column
                    if 'missing' in row.values():
                        message = f"Rij {i+1} is niet verwerkt want deze mist een kolom"
                        messages.add_message(request, messages.WARNING, message)
                        continue

                    # Check if a row has to many values/columns
                    if row.get('excess'):
                        message = f"Rij {i+1} is niet verwerkt want deze heeft teveel kolommen"
                        messages.add_message(request, messages.WARNING, message)
                        continue

                    # Initiatie a location processor with the row data
                    location = LocationProcessor(data=row, user=request.user)
                    try:
                        # Save the locationprocessor instance                        
                        location.save()

                        # Return message for success
                        message = f"Locatie {row['naam']} is geïmporteerd/ge-update."
                        messages.add_message(request, messages.SUCCESS, message)

                    except ValidationError as err:
                        if getattr(err, 'error_list', None):
                            error_messages = [error.message for error in err.error_list]
                        elif getattr(err, 'error_dict', None):
                            error_messages = []
                            for error_list in err.error_dict.values():
                                # Unpredictable fix, because there is a self reference in error_list
                                error_messages.extend([error.messages for error in error_list])
                        else:
                            error_messages = err.message
                        message = f"Fout bij het importeren voor locatie {row['naam']}: {error_messages}"
                        messages.add_message(request, messages.ERROR, message)
            else:
                message = f"{csv_file.name} is geen gelding CSV bestand."
                messages.add_message(request, messages.ERROR, message)
        else:
            message = f"Het formulier is niet juist ingevuld."
            messages.add_message(request, messages.ERROR, message)
        context = {'form': form}
        return render(request, template_name=self.template_name, context=context)        
    

class LocationExportView(View):
    template = 'locations/location-export.html'

    def get(self, request, *args, **kwargs):
        # when a query is given, return the csv file not the webpage
        if request.GET:
            # Get a QuerySet of filtered locations
            locations = Location.objects.search_filter(
                params=self.request.GET.dict(),
                user=self.request.user)
            # Set the response with the csv file
            response = get_csv_file_response(request, locations)
        else:
            response = render(request=request, template_name=self.template)
        return response

    def post(self, request, *args, **kwargs):
        # Get all Location instances()
        locations = Location.objects.all()
        # Set the response with the csv file
        response = get_csv_file_response(request, locations)
        return response


class LocationAdminView(LoginRequiredMixin, View):
    template = 'locations/location-admin.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, template_name=self.template)


class LocationLogView(LoginRequiredMixin, ListView):
    template_name = 'locations/location-log.html'

    def get_queryset(self):
        # Get a QuerySet of filtered locations
        if pandcode := self.kwargs.get('pandcode', None):
            logs = Log.objects.filter(location__pandcode=pandcode)
        else:
            logs = Log.objects.filter(location__isnull=True)
        return logs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if pandcode := self.kwargs.get('pandcode', None):
            context['location'] = Location.objects.get(pandcode=pandcode)
        return context

