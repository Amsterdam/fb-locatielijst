from django.contrib import admin
from locations.models import Location, LocationProperty, PropertyOption, LocationData, ExternalService, LocationExternalService


class PropertyOptionAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(PropertyOptionAdmin, self).get_form(
            request, obj, **kwargs)
        # list only property options of the list type
        form.base_fields['location_property'].queryset = LocationProperty.objects.filter(
            property_type=LocationProperty.LocationPropertyType.CHOICE)
        return form


# Register your models here.
admin.site.register(Location)
admin.site.register(LocationProperty)
admin.site.register(PropertyOption, PropertyOptionAdmin)
admin.site.register(LocationData)
admin.site.register(ExternalService)
admin.site.register(LocationExternalService)
