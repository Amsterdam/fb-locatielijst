from django.contrib import admin
from locations.models import Location, LocationProperty, PropertyOption, LocationData, ExternalService, LocationExternalService


class LocationAdmin(admin.ModelAdmin):
    model = Location
    # overriding fields because otherwise read_only fields appear at the bottom of the native admin form
    fields = ['building_code', 'short_name', 'name', 'description', 'active', 'street', 'street_number',
              'street_number_letter', 'street_number_extension', 'postal_code', 'city', 'construction_year',
               'floor_area', 'longitude', 'latitude', 'rd_x', 'rd_y', 'note', 'last_modified']
    readonly_fields = ['building_code', 'last_modified']


class PropertyOptionAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(PropertyOptionAdmin, self).get_form(
            request, obj, **kwargs)
        # list only property options of the list type
        form.base_fields['location_property'].queryset = LocationProperty.objects.filter(
            property_type__iexact='CHOICE')
        return form


# Register your models here.
admin.site.register(Location, LocationAdmin)
admin.site.register(LocationProperty)
admin.site.register(PropertyOption, PropertyOptionAdmin)
admin.site.register(LocationData)
admin.site.register(ExternalService)
admin.site.register(LocationExternalService)
