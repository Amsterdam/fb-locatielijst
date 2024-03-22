import re
from django.db import models
from django.db.models import Max, Q
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext as _
from locations.managers import LocationManager
# Create your models here.

# Auto generate a new pandcode based on the current highest in the database
def compute_pandcode() -> int:
    return (Location.objects.aggregate(Max('pandcode'))['pandcode__max'] or 0) + 1

def validate_short_name(value)-> str:
    name_regex = '^[a-z]+[0-9a-z_]+$'
    if re.match(name_regex, value):
        return value
    raise ValidationError(
        _("Ongeldige waarde voor: %(value)s"),
        code="invalid",
        params={"value": value},   
    )


class Location(models.Model):
    '''
    Base class for the location
    '''
    pandcode = models.IntegerField(verbose_name='Pandcode', default=compute_pandcode)  # possible race condition when a location is added simultaneously; not worried about it now
    name = models.CharField(verbose_name='Naam', max_length=100)
    last_modified = models.DateTimeField(verbose_name='Laatste wijziging', auto_now=True)
    last_modified_by = models.ForeignKey(User, verbose_name="Laatst gewijzigd door", on_delete=models.PROTECT, null=True, blank=True)
    created_at = models.DateTimeField(verbose_name='Aanmaakdatum', auto_now_add=True)
    is_archived = models.BooleanField(verbose_name="Archief", default=False)
    objects = LocationManager()

    def __str__(self):
        return f'{self.pandcode}, {self.name}'

    class Meta:
        verbose_name = 'Locatie'
        ordering = ['pandcode']
        constraints = [
            models.UniqueConstraint(fields=['pandcode'], name='unique_pandcode'),
            models.UniqueConstraint(fields=['name'], name='unique_name')
        ]
        ordering = ['name']


class PropertyGroup(models.Model):
    name = models.CharField(verbose_name='Groepsnaam', max_length=20)
    order = models.IntegerField(verbose_name='Volgorde', blank=True, null=True, validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = 'Eigenschap groep'
        verbose_name_plural = 'Eigenschap groepen'
        constraints = [
            models.UniqueConstraint(fields=['name'], name='unique_group_name')
        ]

    def __str__(self):
        return f'{self.name}'

class LocationProperty(models.Model):
    '''
    Custom entries for location specific data.
    Each location will have all the extra entries; not every location will have all the entries filled necessarily
    '''
    class LocationPropertyType(models.TextChoices):
        BOOL = 'BOOL', 'Boolean'
        DATE = 'DATE', 'Datum'
        EMAIL = 'EMAIL', 'E-mail'
        GEO = 'GEO', 'Geolocatie'
        NUM = 'NUM', 'Numeriek'
        MEMO = 'MEMO', 'Memo'
        POST = 'POST', 'Postcode'
        STR = 'STR', 'Tekst'
        URL = 'URL', 'Url'
        # Indicates related property option for a choice list
        CHOICE = 'CHOICE', 'Keuzelijst'

    short_name = models.CharField(verbose_name='Korte naam', max_length=10, validators=[validate_short_name])
    label = models.CharField(max_length=100, verbose_name='Omschrijving')
    property_type = models.CharField(verbose_name='Gegevens type', choices=LocationPropertyType.choices, max_length=10)
    required = models.BooleanField(verbose_name='Verplicht veld', default=False)
    multiple = models.BooleanField(verbose_name='Meervoudige invoer', default=False)
    unique = models.BooleanField(verbose_name='Waarde moet uniek zijn', default=False)
    public = models.BooleanField(verbose_name='Zichtbaar voor niet ingelogde gebruikers', default=False)
    group = models.ForeignKey(PropertyGroup, verbose_name='Groeperen in', on_delete=models.SET_NULL, blank=True, null=True)
    order = models.IntegerField(verbose_name='Volgorde', null=True, blank=True, validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = 'Locatie eigenschap'
        verbose_name_plural = 'Locatie eigenschappen'
        constraints = [
            models.UniqueConstraint(fields=['short_name'], name='unique_location_property_name'),
            models.UniqueConstraint(fields=['label'], name='unique_location_property_label')
        ]

    def clean(self):
        super().clean()

        # Only allow multiple == True when property_type == CHOICE
        if self.multiple and self.property_type != 'CHOICE':
            raise ValidationError("Meervoudige invoer is alleen mogelijk bij keuzelijsten.")

    def __str__(self):
        return f'{self.label}'


class PropertyOption(models.Model):
    '''
    Choice list for (some) custom entries 
    '''
    location_property = models.ForeignKey(LocationProperty, on_delete=models.CASCADE, verbose_name='Locatie eigenschap')
    option = models.CharField(verbose_name='Optie', max_length=100)

    class Meta:
        verbose_name = 'Eigenschap optie'
        verbose_name_plural = 'Eigenschappen opties'
        constraints = [models.UniqueConstraint(
            fields=['location_property', 'option'], name='unique_property_option')]

    def __str__(self):
        return f'{self.location_property.label}: {self.option}'


class LocationData(models.Model):
    '''
    Holds each custom data entry for each location
    '''
    location = models.ForeignKey(Location, on_delete=models.CASCADE, verbose_name='Locatie')
    location_property = models.ForeignKey(LocationProperty, on_delete=models.CASCADE, verbose_name='Locatie eigenschap')
    property_option = models.ForeignKey(PropertyOption, on_delete=models.RESTRICT, null=True, blank=True, verbose_name='Optie')
    value = models.TextField(verbose_name='Waarde', max_length=1024, null=True, blank=True)
    last_modified = models.DateTimeField(verbose_name='Laatste wijziging', auto_now=True)
    last_modified_by = models.ForeignKey(User, verbose_name="Laatst gewijzigd door", on_delete=models.PROTECT, null=True, blank=True)
    created_at = models.DateTimeField(verbose_name='Aanmaakdatum', auto_now_add=True)

    class Meta:
        verbose_name = 'Locatie gegeven'
        verbose_name_plural = 'Locatie gegevens'
        constraints = [
            # Constraint so that either property_option or value is filled, or empty
            models.CheckConstraint(
                check=~Q(property_option__isnull=False, value__isnull=False),
                name='either_field_filled',
                violation_error_message=f'Either option or value must be filled.',
            ),
        ]

    def __str__(self):
        return f'{self.location}, {self.location_property}, {self.property_option}, {self.value}'

    def clean(self) -> None:
        # Validate for single instance
        if not self.location_property.multiple and not self.pk:
            if LocationData.objects.filter(location=self.location, location_property=self.location_property).exists():
                raise ValidationError(
                    _("De locatie eigenschap %(property)s bestaat al voor locatie %(location)s."),
                    code='unique',
                    params={
                        'property': self.location_property.label,
                        'location': self.location.pandcode
                    },
                )

        # Validate uniqueness for properties' value
        if self.location_property.unique:
            if LocationData.objects.filter(location_property=self.location_property,value=self.value).exclude(location=self.location).exists():
                raise ValidationError(
                    _("Waarde %(value)s bestaat al voor eigenschap %(property)s."),
                    code='unique',
                    params={
                        'value': self.value,
                        'property': self.location_property.label
                    },
                )

        # Ensure location property validation when submitted via a form
        # Validate for required properties
        if self.location_property.required and not(self.value or self.property_option):
            raise ValidationError(
                _("Waarde verplicht voor %(property)s"),
                code='required',
                params={'property': self.location_property.label}
            )


class ExternalService(models.Model):
    '''
    External data sources (APIs)
    '''
    name = models.CharField(verbose_name='Externe API', max_length=100)
    short_name = models.CharField(verbose_name='Korte naam', max_length=10, validators=[validate_short_name])
    public = models.BooleanField(verbose_name='Zichtbaar voor niet ingelogde gebruikers', default=False)
    order = models.IntegerField(verbose_name='Volgorde', null=True, blank=True, validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = 'Externe koppeling'
        verbose_name_plural = 'Externe koppelingen'
        constraints = [
            models.UniqueConstraint(fields=['name'], name='unique_service_short_name'),
            models.UniqueConstraint(fields=['short_name'], name='unique_service_name')
        ]

    def __str__(self):
        return f'{self.name}'


class LocationExternalService(models.Model):
    '''
    Join table between external services and the location (pandcode) and the external code for the location (externe pandcode)
    '''
    location = models.ForeignKey(Location, on_delete=models.CASCADE, verbose_name='Locatie')
    external_service = models.ForeignKey(ExternalService, on_delete=models.CASCADE, verbose_name='Externe API')
    external_location_code = models.CharField(verbose_name='Externe locatie code', max_length=100, blank=True, null=True)
    last_modified = models.DateTimeField(verbose_name='Laatste wijziging', auto_now=True)
    last_modified_by = models.ForeignKey(User, verbose_name="Laatst gewijzigd door", on_delete=models.PROTECT, null=True, blank=True)
    created_at = models.DateTimeField(verbose_name='Aanmaakdatum', auto_now_add=True)

    class Meta:
        verbose_name = 'Locatie koppeling'
        verbose_name_plural = 'Locatie koppelingen'

    def __str__(self):
        return f'{self.location}, {self.external_service}, {self.external_location_code}'


class Log(models.Model):
    """
    Log model for keeping a log on system and content changes
    """
    timestamp = models.DateTimeField(verbose_name="Tijdstip", auto_now_add=True)
    user = models.ForeignKey(User, verbose_name="Gebruiker", on_delete=models.PROTECT)
    location = models.ForeignKey(Location, verbose_name="Locatie", on_delete=models.CASCADE, null=True, blank=True)
    target = models.CharField(verbose_name="Onderdeel", max_length=100)
    message = models.CharField(verbose_name="Bericht", max_length=1000)

    class Meta:
        verbose_name = 'Locatie log'
        verbose_name_plural = 'Locatie logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.location}, {self.user}, {self.target}, {self.message}'

