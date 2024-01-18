from django import forms
from django.utils.safestring import mark_safe
from locations.models import LocationProperty, ExternalService
from locations.validators import LocationDataValidator


def set_location_property_fields()-> dict:
    fields = dict()
    
    # Get all location properties instances
    location_properties = [obj for obj in LocationProperty.objects.all().order_by('order', 'short_name')]
    
    for location_property in location_properties:

        # Matching the property_type to set the correct form type
        match location_property.property_type:
            case 'BOOL':
                fields[location_property.short_name] = forms.ChoiceField(
                    label=location_property.label,
                    required=location_property.required,
                    choices=(('Ja', 'Ja'),('Nee','Nee')),
                    validators=[LocationDataValidator.valid_boolean],
                )
            case 'DATE':
                fields[location_property.short_name] = forms.CharField(
                    label=location_property.label,
                    required=location_property.required,
                    validators=[LocationDataValidator.valid_date],
                    widget=forms.DateInput
                )
            case 'EMAIL':
                fields[location_property.short_name] = forms.CharField(
                    label=location_property.label,
                    required=location_property.required,
                    validators=[LocationDataValidator.valid_email],
                    widget=forms.EmailInput
                )
            case 'INT':
                fields[location_property.short_name] = forms.CharField(
                    label=location_property.label,
                    required=location_property.required,
                    validators=[LocationDataValidator.valid_integer],
                    widget=forms.NumberInput
                )
            case 'MEMO':
                fields[location_property.short_name] = forms.CharField(
                    label=location_property.label,
                    required=location_property.required,
                    validators=[LocationDataValidator.valid_memo],
                    widget=forms.Textarea)
            case 'POST':
                fields[location_property.short_name] = forms.CharField(
                    label=location_property.label,
                    required=location_property.required,
                    validators=[LocationDataValidator.valid_postal_code],
                    widget=forms.TextInput
                )
            case 'STR':
                fields[location_property.short_name] = forms.CharField(
                    label=location_property.label,
                    required=location_property.required,
                    validators=[LocationDataValidator.valid_string],
                    widget=forms.TextInput
                )
            case 'URL':
                fields[location_property.short_name] = forms.CharField(
                    label=location_property.label,
                    required=location_property.required,
                    validators=[LocationDataValidator.valid_url],
                    widget=forms.URLInput
                )
            case 'CHOICE':
                if location_property.propertyoption_set.values_list('option', flat=True):
                    choice_list = [(option, option) for option in location_property.propertyoption_set.values_list('option', flat=True)]
                else:
                    choice_list = [('', '')]
                fields[location_property.short_name] = forms.ChoiceField(
                    choices=choice_list,
                    label=location_property.label,
                    required=location_property.required,
                )
            case _:
                # If there is no match an exception will be raised
                raise ValueError(f"No form field defined for '{location_property.property_type}'")
    
    return fields

def set_external_services_fields() -> dict:
    fields = dict()

    # Get all extern service instances
    external_services = [obj for obj in ExternalService.objects.all().order_by('short_name')]
    
    # Define a form field for each external service
    for service in external_services:
        fields[service.short_name] = forms.CharField(
            label=service.name,
            required=False,
            validators=[LocationDataValidator.valid_string],
            widget=forms.TextInput
        )
    
    return fields


class LocationDataForm(forms.Form):
    """
    Render the form fields for all location properties from both Location and LocationProperties model
    """
    # Model fields pandcode and last_modified from the Location model are added in the View
    naam = forms.CharField(label='Naam')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add the location property fields to this form
        self.fields.update(set_location_property_fields())

        # Add external services items to this form
        self.fields.update(set_external_services_fields())


class LocationImportForm(forms.Form):
    """Form to import a CSV file with location data"""
    csv_file = forms.FileField(
        required=True, label='CSV bestand',
        help_text=mark_safe('Kies het locatie bronbestand dat je wilt uploaden.')
    )