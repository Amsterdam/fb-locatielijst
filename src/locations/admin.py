from django.contrib import admin
# from django.core.exceptions import ValidationError
# from django.forms.models import BaseInlineFormSet

# from locations.models import (
#     ExternalService,
#     Location,
#     LocationData,
#     LocationExternalService,
#     LocationProperty,
#     Log,
#     PropertyGroup,
#     PropertyOption,
# )


# # Register your models here.
# @admin.register(ExternalService)
# class ExternalServiceAdmin(admin.ModelAdmin):
#     ordering = ["order"]
#     list_display = ["name", "public", "order"]


# @admin.register(Location)
# class LocationAdmin(admin.ModelAdmin):
#     readonly_fields = ["created_at"]


# @admin.register(LocationData)
# class LocationDataAdmin(admin.ModelAdmin): ...


# @admin.register(LocationExternalService)
# class LocationExternalServiceAdmin(admin.ModelAdmin): ...


# @admin.register(PropertyOption)
# class PropertyOptionAdmin(admin.ModelAdmin):
#     ordering = ["location_property__order"]

#     def get_form(self, request, obj=None, **kwargs):
#         form = super().get_form(request, obj, **kwargs)
#         # list only property options of the list type
#         form.base_fields["location_property"].queryset = LocationProperty.objects.filter(
#             property_type=LocationProperty.LocationPropertyType.CHOICE
#         )
#         return form


# class PropertyOptionInlineFormset(BaseInlineFormSet):
#     def clean(self):
#         super().clean()
#         # Raise an error when the user tries to add an option to any other property type than CHOICE
#         if self.instance.property_type != "CHOICE" and len(self.forms) > 0:
#             raise ValidationError("Opties kan je alleen aan een keuzelijst toevoegen.")

#     def save_new(self, form, commit=True):
#         obj = super().save_new(form, commit=False)
#         if commit:
#             obj.save()
#         return obj

#     def save_existing(self, form, instance, commit=True):
#         obj = super().save_existing(form, instance, commit=False)
#         if commit:
#             obj.save()
#         return obj


# class PropertyOptionInline(admin.TabularInline):
#     model = PropertyOption
#     formset = PropertyOptionInlineFormset
#     extra = 0

#     def get_formset(self, request, obj=None, **kwargs):
#         formset = super().get_formset(request, obj, **kwargs)
#         formset.request = request
#         return formset


# @admin.register(LocationProperty)
# class LocationPropertyAdmin(admin.ModelAdmin):
#     ordering = ["group__order", "order"]
#     inlines = [PropertyOptionInline]
#     list_display = ["label", "property_type", "public", "group", "order"]

#     def get_readonly_fields(self, request, obj=None):
#         # Prevent the user from modifying an existing property_type
#         if obj:
#             return self.readonly_fields + ("property_type",)
#         return self.readonly_fields

#     def get_inline_instances(self, request, obj):
#         # Return the inline form only when property_type = CHOICE
#         if not obj:
#             return super().get_inline_instances(request, obj)
#         else:
#             if obj.property_type == "CHOICE":
#                 return super().get_inline_instances(request, obj)
#             else:
#                 return []


# @admin.register(PropertyGroup)
# class PropertyGroupAdmin(admin.ModelAdmin):
#     ordering = ["order"]
#     list_display = ["name", "order"]


# @admin.register(Log)
# class LogAdmin(admin.ModelAdmin):
#     ordering = ["timestamp"]
#     readonly_fields = []
#     list_display = ["timestamp", "user", "content_type", "object_name", "object_id", "action", "field", "message"]

#     def has_add_permission(self, request, obj=None):
#         return False

#     def has_delete_permission(self, request, obj=None):
#         return False


# Custom names
admin.site.site_header = "FB Locatielijst"
admin.site.index_title = "Beheer"
admin.site.site_title = "FB Locatielijst - Beheer"
