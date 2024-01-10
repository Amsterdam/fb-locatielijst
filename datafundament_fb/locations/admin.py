from django.contrib import admin
from locations.models import Location, LocationProperty, PropertyOption, LocationData, ExternalService, LocationExternalService

# Register your models here.
admin.site.register(LocationProperty)
admin.site.register(LocationData)
admin.site.register(ExternalService)
admin.site.register(LocationExternalService)


@admin.register(PropertyOption)
class PropertyOptionAdmin(admin.ModelAdmin):
    ordering = ['location_property__order']

    def get_form(self, request, obj=None, **kwargs):
        form = super(PropertyOptionAdmin, self).get_form(
            request, obj, **kwargs)
        # list only property options of the list type
        form.base_fields['location_property'].queryset = LocationProperty.objects.filter(
            property_type=LocationProperty.LocationPropertyType.CHOICE)
        return form


@admin.register(LocationProperty)
class LocationPropertyAdmin(admin.ModelAdmin):
    ordering = ['order']
