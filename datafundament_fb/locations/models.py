from django.db import models

# Create your models here.
class Location(models.Model):
    '''
    Base class for the location with location typical information
    '''
    building_code = models.CharField(verbose_name='Pandcode',max_length=10) # TODO automatisch generen; hoogste numnme + 1 
    name = models.CharField(verbose_name='Locatie naam',max_length=100)
    description = models.CharField(verbose_name='Beschrijving', max_length=255)
    active = models.BooleanField(verbose_name='Actief')
    last_change = models.DateField(verbose_name='Laatste wijziging') # TODO auto update veld
    street = models.CharField(verbose_name='Straat', max_length=100)
    street_number = models.IntegerField(verbose_name='Straatnummer')
    street_number_extension = models.CharField(
        verbose_name='Toevoeging', max_length=10, null=True, blank=True)  # TODO validator voor postcode??
    postal_code = models.CharField(verbose_name='Postcode', max_length=7)
    city = models.CharField(verbose_name='Plaats', max_length=100)
    construction_year = models.IntegerField(verbose_name='Bouwjaar')
    floor_area = models.IntegerField(verbose_name='Vloeroppervlak')
    longitude = models.FloatField()
    latitude = models.FloatField()
    rd_x = models.FloatField()
    rd_y = models.FloatField()
    note = models.TextField(verbose_name='Notitie')

    def __str__(self):
        return f'{self.building_code}, {self.name}'

    class Meta:
        verbose_name = 'Locatie'


class LocationProperty(models.Model):
    '''
    Custom entries for location specific data.
    Each location will have all the extra entries; not every location will have all the entries filled necessarily
    '''
    order = models.IntegerField(verbose_name='Volgorde')
    label = models.CharField(max_length=100)
    required = models.BooleanField(verbose_name='Verplicht veld')
    multiple = models.BooleanField(verbose_name='Meervoudige invoer')
    description = models.CharField(verbose_name='Locatie data')
    property_type = models.CharField(verbose_name='Gegevens type', max_length=50)

    class Meta:
        verbose_name = 'Locatie eigenschap'
        verbose_name_plural = 'Locatie eigenschappen'


class PropertyOption(models.Model):
    '''
    Choice list for (some) custom entries 
    '''
    location_property = models.ForeignKey(LocationProperty, on_delete=models.PROTECT)
    option = models.CharField(verbose_name='Optie', max_length=100)

    class Meta:
        verbose_name = 'Eigenschap optielijst'
        verbose_name_plural = 'Eigenschappen optielijsten'

class LocationData(models.Model):
    '''
    Holds each custom data entry for each location
    '''
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    location_property = models.ForeignKey(LocationProperty, on_delete=models.PROTECT)
    property_option = models.ForeignKey(PropertyOption, on_delete=models.PROTECT)
    value = models.CharField(verbose_name='Waarde', max_length=255)

    class Meta:
        verbose_name = 'Locatie gegeven'
        verbose_name_plural = 'Locatie gegevens'


class ExternalService(models.Model):
    '''
    External data sources (APIs)
    '''
    name = models.CharField(verbose_name='Externe API', max_length=100)

    class Meta:
        verbose_name = 'Externe koppeling'
        verbose_name_plural = 'Externe koppelingen'


class LocationExternalService(models.Model):
    '''
    Join table between external services and the location (pandcode) and the external code for the location (externe pandcode)
    '''
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    external_service = models.ForeignKey(ExternalService, on_delete=models.CASCADE)
    external_service_entity_id = models.CharField(verbose_name='Externe Id', max_length=100)

    class Meta:
        verbose_name = 'Locatie koppeling'
        verbose_name_plural = 'Locatie koppeling'
