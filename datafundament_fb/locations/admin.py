from django.contrib import admin
from locations.models import Location, LocationProperty, PropertyOption, LocationData, ExternalService, LocationExternalService

# Register your models here.
admin.site.register(Location)
admin.site.register(LocationProperty)
admin.site.register(PropertyOption)
admin.site.register(LocationData)
admin.site.register(ExternalService)
admin.site.register(LocationExternalService)
