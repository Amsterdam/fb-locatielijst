from django import forms
from django.utils.safestring import mark_safe
from locations import validators
from locations.models import LocationProperty
from locations.processors import LocationProcessor


def set_location_property_fields(user: bool=False)-> dict:
    fields = dict()
    
    # Get all location properties instances; filter on public attribute
    location_properties = LocationProcessor(user=user).location_property_instances
    
    for location_property in location_properties:

        # Matching the property_type to set the correct form type
        match location_property.property_type:
            case 'BOOL':
                fields[location_property.short_name] = forms.ChoiceField(
                    label=location_property.label,
                    required=location_property.required,
                    choices=(('Ja', 'Ja'),('Nee','Nee')),
                    validators=[validators.valid_boolean],
                )
            case 'DATE':
                fields[location_property.short_name] = forms.CharField(
                    label=location_property.label,
                    required=location_property.required,
                    validators=[validators.valid_date],
                    widget=forms.DateInput
                )
            case 'EMAIL':
                fields[location_property.short_name] = forms.CharField(
                    label=location_property.label,
                    required=location_property.required,
                    validators=[validators.valid_email],
                    widget=forms.EmailInput
                )
            case 'GEO':
                fields[location_property.short_name] = forms.CharField(
                    label=location_property.label,
                    required=location_property.required,
                    validators=[validators.valid_geolocation],
                    widget=forms.TextInput
                )
            case 'NUM':
                fields[location_property.short_name] = forms.CharField(
                    label=location_property.label,
                    required=location_property.required,
                    validators=[validators.valid_number],
                    widget=forms.TextInput
                )
            case 'MEMO':
                fields[location_property.short_name] = forms.CharField(
                    label=location_property.label,
                    required=location_property.required,
                    validators=[validators.valid_memo],
                    widget=forms.Textarea)
            case 'POST':
                fields[location_property.short_name] = forms.CharField(
                    label=location_property.label,
                    required=location_property.required,
                    validators=[validators.valid_postal_code],
                    widget=forms.TextInput
                )
            case 'STR':
                fields[location_property.short_name] = forms.CharField(
                    label=location_property.label,
                    required=location_property.required,
                    validators=[validators.valid_string],
                    widget=forms.TextInput
                )
            case 'URL':
                fields[location_property.short_name] = forms.CharField(
                    label=location_property.label,
                    required=location_property.required,
                    validators=[validators.valid_url],
                    widget=forms.URLInput
                )
            case 'CHOICE':
                # Fill option list with related PropertyOptions
                if (options := location_property.propertyoption_set.values_list('option', flat=True)):
                    choice_list = [(option, option) for option in options]
                else:
                    choice_list = []

                # For multiple choice fileds, select the appropriate field and widget
                if location_property.multiple:
                    fields[location_property.short_name] = forms.MultipleChoiceField(
                        choices=choice_list,
                        label=location_property.label,
                        required=location_property.required,
                        widget=forms.CheckboxSelectMultiple,
                        validators=[validators.ChoiceValidator(location_property)]
                    )
                else:
                    fields[location_property.short_name] = forms.ChoiceField(
                        choices=choice_list,
                        label=location_property.label,
                        required=location_property.required,
                        validators=[validators.ChoiceValidator(location_property)]
                    )
            case _:
                # If there is no match an exception will be raised
                raise ValueError(f"Er bestaat geen formulierveld voor '{location_property.property_type}'.")

        # Add the property group to the field
        fields[location_property.short_name].group = getattr(location_property.group, 'name', 'Overig')

    return fields

def set_external_services_fields(user: bool=False) -> dict:
    fields = dict()

    # Get all external service instances; filter on public attribute
    external_services = LocationProcessor(user=user).external_service_instances
    
    # Define a form field for each external service
    for service in external_services:
        fields[service.short_name] = forms.CharField(
            label=service.name,
            required=False,
            validators=[validators.valid_string],
            widget=forms.TextInput
        )
        fields[service.short_name].group = 'Externe koppelingen'
        
    return fields


class LocationDataForm(forms.Form):
    """
    Render the form fields for all location properties from both Location and LocationProperties model
    """
    # Model fields pandcode and last_modified from the Location model are added in the View

    def __init__(self, *args, **kwargs):
        # Set and remove pandcode and user argument before calling init
        pandcode = kwargs.pop('pandcode', None)
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Add location name field for custom validation
        self.fields['naam'] = forms.CharField(
            label='Naam',
            required=True,
            validators=[validators.LocationNameValidator(pandcode=pandcode)],
            widget=forms.TextInput,
        )

        # Add the location property fields to this form
        self.fields.update(set_location_property_fields(user=user))

        # Add external services items to this form
        self.fields.update(set_external_services_fields(user=user))


class LocationImportForm(forms.Form):
    """Form to import a CSV file with location data"""
    csv_file = forms.FileField(
        required=True, label='CSV bestand',
        help_text=mark_safe('Kies het locatie bronbestand dat je wilt uploaden.')
    )


class LocationListForm(forms.Form):
    
    def __init__(self, *args, **kwargs):
        # Set and remove user argument before calling init
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
   
        # Get all LocationProperty and ExternalService objects 
        location_properties = LocationProcessor(user=user).location_property_instances
        external_services = LocationProcessor(user=user).external_service_instances
        
        # Create a list of location properties to search in and an option to search in all properties
        property_list = [('','Alle tekstvelden'),('naam','Naam'),('pandcode','Pandcode')]
        property_list.extend([(property.short_name, property.label) for property in location_properties])
        property_list.extend([(property.short_name, property.name) for property in external_services])
        # Create the select field with the property choices
        self.fields['property'] = forms.ChoiceField(
            label='Waar wil je zoeken',
            choices=property_list,
            widget=forms.Select(attrs={'onchange': 'setSearchField();'}),
        )

        # Create a search textfield 
        self.fields['search'] = forms.CharField(
            label='Wat wil je zoeken',
        )

        # Create selection lists for any LocationProperty which has the property_type 'CHOICE'
        for location_property in LocationProperty.objects.filter(property_type='CHOICE'):
            # Only process properties from the location_properties list; because this is list is filtered for access permission 
            if location_property in location_properties:
                # Get all options for the location property
                options = location_property.propertyoption_set.values_list('option', flat=True)
                # Create a choice list from the options
                options_list = [(option, option) for option in options]
                if options_list:
                    # Add the selection field to the form
                    self.fields[location_property.short_name] = forms.ChoiceField(
                        label='Wat wil je zoeken',
                        choices=options_list
                    )            

        # Add a selection field to the form to filter on archived locations
        archive_list = [('active', 'Actief'),('archived', 'Gearchiveerd'),('all', 'Alle')]
        self.fields['archive'] = forms.ChoiceField(
            label='Archief',
            choices=archive_list,
        )

