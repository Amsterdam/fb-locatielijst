from django.db import models
from django.db.models import Max

# Create your models here.

# Auto generate a new building_code based on the current highest in the database
def compute_building_code() -> int:
    return (Location.objects.aggregate(Max('building_code'))['building_code__max'] or 0) + 1


class Location(models.Model):
    '''
    Base class for the location with location typical information
    '''
    building_code = models.IntegerField(
        verbose_name='Pandcode', default=compute_building_code) # possible race condition when a location is added simultaneously; not worried about it now
    short_name = models.CharField(verbose_name='Afkorting', max_length=12, null=True, blank=True)
    name = models.CharField(verbose_name='Locatie',max_length=100,)
    description = models.CharField(
        verbose_name='Beschrijving', max_length=255)
    active = models.BooleanField(verbose_name='Actief', default=True)
    last_modified = models.DateField(verbose_name='Laatste wijziging', auto_now=True)
    street = models.CharField(verbose_name='Straat', max_length=100)
    street_number = models.IntegerField(verbose_name='Straatnummer')
    street_number_letter = models.CharField(
        verbose_name='Huisletter', max_length=10, null=True, blank=True)
    street_number_extension = models.CharField(
        verbose_name='Nummer toevoeging', max_length=10, null=True, blank=True)
    postal_code = models.CharField(verbose_name='Postcode', max_length=7)
    city = models.CharField(verbose_name='Plaats', max_length=100)
    construction_year = models.IntegerField(verbose_name='Bouwjaar', null=True, blank=True)
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
            models.UniqueConstraint(fields=['building_code'], name='unique_building_code'),
            models.UniqueConstraint(fields=['name'], name='unique_location_name')
        ]


class LocationPropertyType(models.TextChoices):
    BOOL = "BOOL", "Boolean"
    DATE = "DATE", "Datum"
    INT = "INT", "Numeriek"
    STR = "STR", "Tekst"
    CHOICE = "CHOICE", "Keuzelijst" # Indicates related property option for a choice list


class LocationProperty(models.Model):
    '''
    Custom entries for location specific data.
    Each location will have all the extra entries; not every location will have all the entries filled necessarily
    '''
    order = models.IntegerField(verbose_name='Volgorde', null=True, blank=True)
    label = models.CharField(max_length=100)
    required = models.BooleanField(verbose_name='Verplicht veld')
    multiple = models.BooleanField(verbose_name='Meervoudige invoer')
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
    location_property = models.ForeignKey(LocationProperty, on_delete=models.CASCADE)
    option = models.CharField(verbose_name='Optie', max_length=100)

    class Meta:
        verbose_name = 'Eigenschap optie'
        verbose_name_plural = 'Eigenschappen opties'
        constraints = [models.UniqueConstraint(
            fields=['location_property','option'], name='unique_property_option')]

    def __str__(self):
        return f'{self.location_property}, {self.option}'


class LocationData(models.Model):
    '''
    Holds each custom data entry for each location
    '''
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    location_property = models.ForeignKey(LocationProperty, on_delete=models.CASCADE)
    property_option = models.ForeignKey(PropertyOption, on_delete=models.PROTECT)
    value = models.CharField(verbose_name='Waarde', max_length=255)

    class Meta:
        verbose_name = 'Locatie gegeven'
        verbose_name_plural = 'Locatie gegevens'

    def __str__(self):
        return f'{self.location}, {self.location_property}, {self.property_option}, {self.value} '


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
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    external_service = models.ForeignKey(ExternalService, on_delete=models.CASCADE)
    external_location_code = models.CharField(verbose_name='Externe locatie code', max_length=100)

    class Meta:
        verbose_name = 'Locatie koppeling'
        verbose_name_plural = 'Locatie koppeling'

    def __str__(self):
        return f'{self.location}, {self.external_service}, {self.external_code} '