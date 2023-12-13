import re
from django.db import models
from django.db.models import Max, Q
from django.core.exceptions import ValidationError
from locations.validators import LocationDataValidator

# Create your models here.

# Auto generate a new building_code based on the current highest in the database
def compute_building_code() -> int:
    return (Location.objects.aggregate(Max('building_code'))['building_code__max'] or 0) + 1

def validate_postal_code(value)-> str:
    postal_code_regex = '^[1-9][0-9]{3}\s?(?!SA|SD|SS)[A-Z]{2}$'
    if re.match(postal_code_regex, value):
        return value
    else:
        raise ValidationError("This is not a valid postal code in the format 0000XX")


class Location(models.Model):
    '''
    Base class for the location with location typical information
    '''
    building_code = models.IntegerField(
        verbose_name='Pandcode', default=compute_building_code)  # possible race condition when a location is added simultaneously; not worried about it now
    short_name = models.CharField(
        verbose_name='Afkorting', max_length=12, null=True, blank=True)
    name = models.CharField(verbose_name='Locatie', max_length=100,)
    description = models.CharField(
        verbose_name='Beschrijving', max_length=255)
    active = models.BooleanField(verbose_name='Actief', default=True)
    last_modified = models.DateField(
        verbose_name='Laatste wijziging', auto_now=True)
    street = models.CharField(verbose_name='Straat', max_length=100)
    street_number = models.IntegerField(verbose_name='Straatnummer')
    street_number_letter = models.CharField(
        verbose_name='Huisletter', max_length=10, null=True, blank=True)
    street_number_extension = models.CharField(
        verbose_name='Nummer toevoeging', max_length=10, null=True, blank=True)
    postal_code = models.CharField(verbose_name='Postcode', max_length=7, validators=[validate_postal_code])
    city = models.CharField(verbose_name='Plaats', max_length=100)
    construction_year = models.IntegerField(
        verbose_name='Bouwjaar', null=True, blank=True)
    floor_area = models.IntegerField(
        verbose_name='Vloeroppervlak', null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    rd_x = models.FloatField(null=True, blank=True)
    rd_y = models.FloatField(null=True, blank=True)
    note = models.TextField(verbose_name='Notitie', null=True, blank=True)

    def __str__(self):
        return f'{self.building_code}, {self.name}'

    class Meta:
        verbose_name = 'Locatie'
        constraints = [
            models.UniqueConstraint(
                fields=['building_code'], name='unique_building_code'),
            models.UniqueConstraint(
                fields=['name'], name='unique_location_name')
        ]


class LocationProperty(models.Model):
    '''
    Custom entries for location specific data.
    Each location will have all the extra entries; not every location will have all the entries filled necessarily
    '''
    class LocationPropertyType(models.TextChoices):
        BOOL = 'BOOL', 'Boolean'
        DATE = 'DATE', 'Datum'
        EMAIL = 'EMAIL', 'E-mail'
        INT = 'INT', 'Numeriek'
        STR = 'STR', 'Tekst'
        URL = 'URL', 'Url'
        # Indicates related property option for a choice list
        CHOICE = 'CHOICE', 'Keuzelijst'

    order = models.IntegerField(verbose_name='Volgorde', null=True, blank=True)
    label = models.CharField(max_length=100)
    required = models.BooleanField(
        verbose_name='Verplicht veld', default=False)
    multiple = models.BooleanField(
        verbose_name='Meervoudige invoer', default=False)
    description = models.CharField(
        verbose_name='Omschrijving', null=True, blank=True, max_length=255)
    property_type = models.CharField(
        verbose_name='Gegevens type', choices=LocationPropertyType.choices, max_length=10)

    class Meta:
        verbose_name = 'Locatie eigenschap'
        verbose_name_plural = 'Locatie eigenschappen'

    def __str__(self):
        required = ', verplicht' if self.required else ''
        multiple = ', meervoudig' if self.multiple else ''
        return f'{self.label} ({self.property_type}){required}{multiple}'


class PropertyOption(models.Model):
    '''
    Choice list for (some) custom entries 
    '''
    location_property = models.ForeignKey(
        LocationProperty, on_delete=models.CASCADE, verbose_name='Locatie eigenschap')
    option = models.CharField(verbose_name='Optie', max_length=100)

    class Meta:
        verbose_name = 'Eigenschap optie'
        verbose_name_plural = 'Eigenschappen opties'
        constraints = [models.UniqueConstraint(
            fields=['location_property', 'option'], name='unique_property_option')]

    def __str__(self):
        return f'{self.location_property}, {self.option}'


class LocationData(models.Model):
    '''
    Holds each custom data entry for each location
    '''
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, verbose_name='Locatie')
    location_property = models.ForeignKey(
        LocationProperty, on_delete=models.CASCADE, verbose_name='Locatie eigenschap')
    property_option = models.ForeignKey(
        PropertyOption, on_delete=models.PROTECT, null=True, blank=True, verbose_name='Optie')
    value = models.CharField(verbose_name='Waarde', max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = 'Locatie gegeven'
        verbose_name_plural = 'Locatie gegevens'
        constraints = [
            # Constraint so that either property_option or value is filled
            models.CheckConstraint(
                check=Q(property_option__isnull=False, value__isnull=True) | Q(
                    property_option__isnull=True, value__isnull=False),
                name='either_field_filled',
                violation_error_message=f'Either option or value must be filled.',
            ),
        ]

    def __str__(self):
        return f'{self.location}, {self.location_property}, {self.property_option}, {self.value}'

    def clean(self) -> None:
        # Ensure location property validation when submitted via a form
        # Skip for choice validation, because value should be empty
        if self.location_property.property_type != 'CHOICE': 
            LocationDataValidator().validate(
                location_property=self.location_property, value=self.value)


class ExternalService(models.Model):
    '''
    External data sources (APIs)
    '''
    name = models.CharField(verbose_name='Externe API', max_length=100)

    class Meta:
        verbose_name = 'Externe koppeling'
        verbose_name_plural = 'Externe koppelingen'

    def __str__(self):
        return f'{self.name}'


class LocationExternalService(models.Model):
    '''
    Join table between external services and the location (pandcode) and the external code for the location (externe pandcode)
    '''
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, verbose_name='Locatie')
    external_service = models.ForeignKey(
        ExternalService, on_delete=models.CASCADE, verbose_name='Externe API')
    external_location_code = models.CharField(
        verbose_name='Externe locatie code', max_length=100)

    class Meta:
        verbose_name = 'Locatie koppeling'
        verbose_name_plural = 'Locatie koppeling'

    def __str__(self):
        return f'{self.location}, {self.external_service}, {self.external_location_code} '
