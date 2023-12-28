from django import forms
from locations.models import Location
from locations.validators import LocationDataValidator
from locations.models import LocationProperty

class LocationDetailForm(forms.Form):
    pandcode = forms.IntegerField() # TODO hoe kan dit read-only zijn? Zie bijv: https://www.google.com/search?client=firefox-b-d&q=django+request.POST+disabled+field+is+empty
    naam = forms.CharField(label='Locatie')
    #mut_datum = forms.DateField(label='Laatste wijziging', disabled=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        location_properties = [obj for obj in LocationProperty.objects.all()]
        for location_property in location_properties:
            match location_property.property_type:
                case 'BOOL':
                    self.fields[location_property.short_name] = forms.TypedChoiceField(
                        label=location_property.label,
                        required=location_property.required,
                        choices=(('Ja', 'Ja'),('Nee','Nee')),
                        validators=[LocationDataValidator.valid_boolean]
                    )
                case 'DATE':
                    self.fields[location_property.short_name] = forms.CharField(
                        label=location_property.label,
                        required=location_property.required,
                        validators=[LocationDataValidator.valid_date]
                    )
                case 'EMAIL':
                    self.fields[location_property.short_name] = forms.CharField(
                        label=location_property.label,
                        required=location_property.required,
                        validators=[LocationDataValidator.valid_email])
                case 'INT':
                    self.fields[location_property.short_name] = forms.CharField(
                        label=location_property.label,
                        required=location_property.required,
                        validators=[LocationDataValidator.valid_integer])
                case 'MEMO':
                    self.fields[location_property.short_name] = forms.CharField(
                        label=location_property.label,
                        required=location_property.required,
                        validators=[LocationDataValidator.valid_memo])
                case 'POST':
                    self.fields[location_property.short_name] = forms.CharField(
                        label=location_property.label,
                        required=location_property.required,
                        validators=[LocationDataValidator.valid_postal_code])
                case 'STR':
                    self.fields[location_property.short_name] = forms.CharField(
                        label=location_property.label,
                        required=location_property.required,
                        validators=[LocationDataValidator.valid_string])
                case 'URL':
                    self.fields[location_property.short_name] = forms.CharField(
                        label=location_property.label,
                        required=location_property.required,
                        validators=[LocationDataValidator.valid_url]
                    )
                case 'CHOICE':
                    if location_property.propertyoption_set.values_list('option', flat=True):
                        choice_list = [(option, option) for option in location_property.propertyoption_set.values_list('option', flat=True)]
                    else:
                        choice_list = [('', 'Keuzelijst is leeg')] # TODO HOE OM TE GAAN MET LEGE CHOICE VELDEN, OF MOGEN DIE NIET BESTAAN?
                    self.fields[location_property.short_name] = forms.ChoiceField(
                        choices=choice_list,
                        label=location_property.label,
                        required=location_property.required,
                        # TODO VALIDATIE NODIG?
                    )
        
        
    
