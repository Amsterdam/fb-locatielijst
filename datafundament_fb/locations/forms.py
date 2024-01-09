from django import forms
from django.utils.safestring import mark_safe
from locations.models import LocationProperty
from locations.validators import LocationDataValidator

def set_location_property_fields()-> dict:
    fields = dict()
    location_properties = [obj for obj in LocationProperty.objects.all().order_by('order', 'short_name')]
    for location_property in location_properties:
        match location_property.property_type:
            case 'BOOL':
                fields[location_property.short_name] = forms.TypedChoiceField(
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
                    choice_list = [('', '')] # TODO HOE OM TE GAAN MET LEGE CHOICE VELDEN, OF MOGEN DIE NIET BESTAAN?
                fields[location_property.short_name] = forms.ChoiceField(
                    choices=choice_list,
                    label=location_property.label,
                    required=location_property.required,
                    # TODO VALIDATIE NODIG?
                )

    return fields


class LocationDetailForm(forms.Form):
    # pandcode = forms.IntegerField(label='Pandcode) # TODO hoe kan dit read-only zijn? Zie bijv: https://www.google.com/search?client=firefox-b-d&q=django+request.POST+disabled+field+is+empty
    naam = forms.CharField(label='Naam')
    #last_modified = forms.DateField(label='Laatste wijziging', disabled=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # if kwargs.get('initial'):
        #     add_fields_to_top = {
        #         'pandcode' : forms.IntegerField(label='Pandcode', disabled=True),
        #         'last_modified' : forms.DateField(label='Laatste wijziging', disabled=True)
        #     }
        #     add_fields_to_top.update(self.fields)
        #     self.fields = add_fields_to_top        
        
        self.fields.update(set_location_property_fields())