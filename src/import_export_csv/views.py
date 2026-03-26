from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render
from django.views.generic import View

from import_export_csv.forms import LocatieImportForm
from import_export_csv.handle_import import handle_import_csv
from .exporter import get_csv_response, fetch_locations_for_export

class LocationExportView(LoginRequiredMixin, View):
    template = "import_export_csv/locatie-export.html"

    def get(self, request, *args, **kwargs):
        if request.GET:
            all_locations = fetch_locations_for_export()
            return get_csv_response(all_locations)
        return render(request=request, template_name=self.template)

    def post(self, request, *args, **kwargs):
        all_locations = fetch_locations_for_export()
        return get_csv_response(all_locations)


class IsStaffMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class LocatieImportView(LoginRequiredMixin, IsStaffMixin, View):
    form = LocatieImportForm
    template_name = "import_export_csv/locatie-import.html"

    def get(self, request):
        form = self.form()
        context = {"form": form}

        return render(request, template_name=self.template_name, context=context)

    def post(self, request):
        form = self.form(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data.get("csv_file")
            location_added = handle_import_csv(request, csv_file)
        else:
            message = "Het formulier is niet juist ingevuld."
            messages.add_message(request, messages.ERROR, message)
            location_added = 0

        context = {"form": form}
        if location_added > 0:
            # Message for succesful imports
            message = f"{location_added} locatie(s) geïmporteerd/ge-update."
            messages.add_message(request, messages.SUCCESS, message)
        return render(request, template_name=self.template_name, context=context)


# class LocationExportView(LoginRequiredMixin, View):
#     template = "import_export_csv/location-export.html"

#     def get(self, request, *args, **kwargs):
#         # when a query is given, return the csv file not the webpage
#         if request.GET:
#             # # Get a QuerySet of filtered locations
#             # locations = Location.objects.search_filter(params=self.request.GET.dict(), user=self.request.user)
#             # # Set the response with the csv file
#             # response = get_csv_file_response(request, locations)
#             print("testGet")
#         else:
#             response = render(request=request, template_name=self.template)
#         return response

#     def post(self, request, *args, **kwargs):
#         # # Get all Location instances()
#         # locations = Location.objects.search_filter(params=dict(), user=self.request.user)
#         # # Set the response with the csv file
#         # response = get_csv_file_response(request, locations)
#         print("exporting!!")
#         return response