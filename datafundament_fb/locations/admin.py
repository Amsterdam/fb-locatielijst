from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from locations.models import Location, LocationProperty, PropertyOption, LocationData, ExternalService, LocationExternalService

# Register your models here.
@admin.register(ExternalService)
class ExternalServiceAdmin(admin.ModelAdmin):...


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    readonly_fields = ['last_modified', 'created_at']


@admin.register(LocationData)
class LocationDataAdmin(admin.ModelAdmin):
    readonly_fields = ['last_modified', 'created_at']


@admin.register(LocationExternalService)
class LocationExternalServiceAdmin(admin.ModelAdmin):
    readonly_fields = ['last_modified', 'created_at']


@admin.register(PropertyOption)
class PropertyOptionAdmin(admin.ModelAdmin):
    ordering = ['location_property__order']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(
            request, obj, **kwargs)
        # list only property options of the list type
        form.base_fields['location_property'].queryset = LocationProperty.objects.filter(
            property_type=LocationProperty.LocationPropertyType.CHOICE)
        return form


class PropertyOptionInlineFormset(BaseInlineFormSet):
    def clean(self):
        super().clean()
        # Raise an error when the user tries to add an option to any other property type than CHOICE
        if self.instance.property_type != 'CHOICE' and len(self.forms) > 0:
            raise ValidationError("Opties kan je alleen aan een keuzelijst toevoegen.")


class PropertyOptionInline(admin.TabularInline):
    model = PropertyOption
    formset = PropertyOptionInlineFormset
    extra = 0


@admin.register(LocationProperty)
class LocationPropertyAdmin(admin.ModelAdmin):
    ordering = ['order']
    inlines = [PropertyOptionInline]

    def get_readonly_fields(self, request, obj=None):
        # Prevent the user from modifying an existing property_type 
        if obj:
            return self.readonly_fields + ('property_type',)
        return self.readonly_fields
    
    def get_inline_instances(self, request, obj):
        # Return the inline form only when property_type = CHOICE
        if not obj:
            return super().get_inline_instances(request, obj)
        else:
            if obj.property_type == 'CHOICE':
                return super().get_inline_instances(request, obj)
            else:
                return []
        
# Custom names
admin.site.site_header = 'Datafundament Facilitair Bureau'
admin.site.index_title = 'Beheer'
admin.site.site_title = 'Datafundament Facilitair Bureau - Beheer'