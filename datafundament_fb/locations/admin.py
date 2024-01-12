from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from locations.models import Location, LocationProperty, PropertyOption, LocationData, ExternalService, LocationExternalService

# Register your models here.
admin.site.register(Location)
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


class PropertyOptionInlineFormset(BaseInlineFormSet):
    def clean(self):
        super(PropertyOptionInlineFormset, self).clean()
        if self.instance.property_type != 'CHOICE' and len(self.forms) > 0:
            raise ValidationError("Opties kan je alleen aan een Keuzelijst toevoegen")


class PropertyOptionInline(admin.TabularInline):
    model = PropertyOption
    formset = PropertyOptionInlineFormset
    extra = 0


@admin.register(LocationProperty)
class LocationPropertyAdmin(admin.ModelAdmin):
    ordering = ['order']
    inlines = [PropertyOptionInline]

    def get_readonly_fields(self, request, obj=None):
        if obj: # editing an existing object
            return self.readonly_fields + ('property_type',)
        return self.readonly_fields
    
    def get_inline_instances(self, request, obj):
        #Return inlines only when property_type = choice
        if not obj:
            return super(LocationPropertyAdmin, self).get_inline_instances(request, obj)
        else:
            if obj.property_type == 'CHOICE':
                return super(LocationPropertyAdmin, self).get_inline_instances(request, obj)
            else:
                return []
        