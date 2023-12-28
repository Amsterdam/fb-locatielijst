from django import forms
from locations.processors import LocationDataProcessor
from locations.models import Location, validate_postal_code
from locations.validators import LocationDataValidator
from locations.models import LocationProperty

class LocationDetailForm(forms.Form):
    building_code = forms.IntegerField(label='Pandcode') # TODO hoe kan dit read-only zijn? Zie bijv: https://www.google.com/search?client=firefox-b-d&q=django+request.POST+disabled+field+is+empty
    short_name = forms.CharField(label='Afkorting', required=False)
    name = forms.CharField(label='Locatie')
    description = forms.CharField(label='Beschrijving')
    active = forms.ChoiceField(label='Actief', choices=Location.ACTIVE_CHOICES)
    last_modified = forms.DateField(label='Laatste wijziging')
    street = forms.CharField(label='Straat')
    street_number = forms.IntegerField(label='Straatnummer')
    street_number_letter = forms.CharField(label='Huisletter', required=False)
    street_number_extension = forms.CharField(label="Nummer toevoeging", required=False)
    postal_code = forms.CharField(label='Postcode', validators=[validate_postal_code])
    city = forms.CharField(label='Plaats')
    construction_year = forms.IntegerField(label='Bouwjaar', required=False)
    floor_area = forms.IntegerField(label='Vloeroppervlak', required=False)
    longitude = forms.FloatField(required=False)
    latitude = forms.FloatField(required=False)
    rd_x = forms.FloatField(required=False)
    rd_y = forms.FloatField(required=False)
    note = forms.CharField(widget=forms.Textarea(attrs={"rows":"5"}), required=False)

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
        
        
    
