import re

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Max, Q
from django.utils.translation import gettext as _

from locations.managers import LocationManager

# Create your models here.


# Auto generate a new pandcode based on the current highest in the database
def compute_pandcode() -> int:
    return (Location.objects.aggregate(Max("pandcode"))["pandcode__max"] or 0) + 1


def validate_short_name(value) -> str:
    name_regex = "^[a-z]+[0-9a-z_]+$"
    if re.match(name_regex, value):
        return value
    raise ValidationError(
        _("Ongeldige waarde voor: %(value)s"),
        code="invalid",
        params={"value": value},
    )


class Location(models.Model):
    """
    Base class for the location
    """

    pandcode = models.IntegerField(
        verbose_name="Pandcode", default=compute_pandcode
    )  # possible race condition when a location is added simultaneously; not worried about it now
    name = models.CharField(verbose_name="Naam", max_length=100)
    last_modified = models.DateTimeField(verbose_name="Laatste wijziging", auto_now=True)
    created_at = models.DateTimeField(verbose_name="Aanmaakdatum", auto_now_add=True)
    is_archived = models.BooleanField(verbose_name="Archief", default=False)
    objects = LocationManager()

    def __str__(self):
        return f"{self.pandcode}, {self.name}"

    class Meta:
        verbose_name = "Locatie"
        ordering = ["pandcode"]
        constraints = [
            models.UniqueConstraint(fields=["pandcode"], name="unique_pandcode"),
            models.UniqueConstraint(fields=["name"], name="unique_name"),
        ]


class PropertyGroup(models.Model):
    name = models.CharField(verbose_name="Groepsnaam", max_length=20)
    order = models.IntegerField(verbose_name="Volgorde", blank=True, null=True, validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = "Eigenschap groep"
        verbose_name_plural = "Eigenschap groepen"
        constraints = [models.UniqueConstraint(fields=["name"], name="unique_group_name")]

    def __str__(self):
        return f"{self.name}"


class LocationProperty(models.Model):
    """
    Custom entries for location specific data.
    Each location will have all the extra entries; not every location will have all the entries filled necessarily
    """

    class LocationPropertyType(models.TextChoices):
        BOOL = "BOOL", "Boolean"
        DATE = "DATE", "Datum"
        EMAIL = "EMAIL", "E-mail"
        GEO = "GEO", "Geolocatie"
        NUM = "NUM", "Numeriek"
        MEMO = "MEMO", "Memo"
        POST = "POST", "Postcode"
        STR = "STR", "Tekst"
        URL = "URL", "Url"
        # Indicates related property option for a choice list
        CHOICE = "CHOICE", "Keuzelijst"

    short_name = models.CharField(verbose_name="Korte naam", max_length=10, validators=[validate_short_name])
    label = models.CharField(max_length=100, verbose_name="Omschrijving")
    property_type = models.CharField(verbose_name="Gegevens type", choices=LocationPropertyType.choices, max_length=10)
    required = models.BooleanField(verbose_name="Verplicht veld", default=False)
    multiple = models.BooleanField(verbose_name="Meervoudige invoer", default=False)
    unique = models.BooleanField(verbose_name="Waarde moet uniek zijn", default=False)
    public = models.BooleanField(verbose_name="Zichtbaar voor niet ingelogde gebruikers", default=False)
    group = models.ForeignKey(
        PropertyGroup, verbose_name="Groeperen in", on_delete=models.SET_NULL, blank=True, null=True
    )
    order = models.IntegerField(verbose_name="Volgorde", null=True, blank=True, validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = "Locatie eigenschap"
        verbose_name_plural = "Locatie eigenschappen"
        ordering = [F("group__order").asc(nulls_last=True), "order"]
        constraints = [
            models.UniqueConstraint(fields=["short_name"], name="unique_location_property_name"),
            models.UniqueConstraint(fields=["label"], name="unique_location_property_label"),
        ]

    def clean(self):
        super().clean()

        # Only allow multiple == True when property_type == CHOICE
        if self.multiple and self.property_type != "CHOICE":
            raise ValidationError("Meervoudige invoer is alleen mogelijk bij keuzelijsten.")

    def __str__(self):
        return f"{self.label}"


class PropertyOption(models.Model):
    """
    Choice list for (some) custom entries
    """

    location_property = models.ForeignKey(LocationProperty, on_delete=models.CASCADE, verbose_name="Locatie eigenschap")
    option = models.CharField(verbose_name="Optie", max_length=100)

    class Meta:
        verbose_name = "Eigenschap optie"
        verbose_name_plural = "Eigenschappen opties"
        ordering = ["option"]
        constraints = [models.UniqueConstraint(fields=["location_property", "option"], name="unique_property_option")]

    def __str__(self):
        return f"{self.location_property.label}: {self.option}"


class LocationData(models.Model):
    """
    Holds each custom data entry for each location
    """

    location = models.ForeignKey(Location, on_delete=models.CASCADE, verbose_name="Locatie")
    location_property = models.ForeignKey(LocationProperty, on_delete=models.CASCADE, verbose_name="Locatie eigenschap")
    _property_option = models.ForeignKey(
        PropertyOption, on_delete=models.RESTRICT, null=True, blank=True, verbose_name="Optie"
    )
    _value = models.TextField(verbose_name="Waarde", max_length=1024, null=True, blank=True)

    class Meta:
        verbose_name = "Locatie gegeven"
        verbose_name_plural = "Locatie gegevens"
        ordering = ["id"]
        constraints = [
            # Constraint so that either property_option or value is filled, or empty
            models.CheckConstraint(
                check=~Q(_property_option__isnull=False, _value__isnull=False),
                name="either_field_filled",
                violation_error_message=f"Either option or value must be filled.",
            ),
        ]

    # Property to get/set a value for either _property_option or _value
    @property
    def value(self):
        if self.location_property.property_type == "CHOICE" and self._property_option:
            return self._property_option.option
        else:
            return self._value

    @value.setter
    def value(self, value):
        if self.location_property.property_type == "CHOICE" and value:
            option = PropertyOption.objects.filter(location_property=self.location_property, option=value).first()
            self._property_option = option
        else:
            self._value = value

    def __str__(self):
        return f"{self.location}, {self.location_property}, {self.value}"

    def clean(self) -> None:
        # Validate for single instance
        if not self.location_property.multiple and not self.pk:
            if LocationData.objects.filter(location=self.location, location_property=self.location_property).exists():
                raise ValidationError(
                    _("De locatie eigenschap %(property)s bestaat al voor locatie %(location)s."),
                    code="unique",
                    params={"property": self.location_property.label, "location": self.location.pandcode},
                )

        # Validate uniqueness for properties' value
        if self.location_property.unique:
            if (
                LocationData.objects.filter(location_property=self.location_property, _value=self._value)
                .exclude(location=self.location)
                .exists()
            ):
                raise ValidationError(
                    _("Waarde %(value)s bestaat al voor eigenschap %(property)s."),
                    code="unique",
                    params={"value": self._value, "property": self.location_property.label},
                )

        # Ensure location property validation when submitted via a form
        # Validate for required properties
        if self.location_property.required and not (self.value):
            raise ValidationError(
                _("Waarde verplicht voor %(property)s"),
                code="required",
                params={"property": self.location_property.label},
            )


class ExternalService(models.Model):
    """
    External data sources (APIs)
    """

    name = models.CharField(verbose_name="Externe API", max_length=100)
    short_name = models.CharField(verbose_name="Korte naam", max_length=10, validators=[validate_short_name])
    public = models.BooleanField(verbose_name="Zichtbaar voor niet ingelogde gebruikers", default=False)
    order = models.IntegerField(verbose_name="Volgorde", null=True, blank=True, validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = "Externe koppeling"
        verbose_name_plural = "Externe koppelingen"
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["name"], name="unique_service_short_name"),
            models.UniqueConstraint(fields=["short_name"], name="unique_service_name"),
        ]

    def __str__(self):
        return f"{self.name}"


class LocationExternalService(models.Model):
    """
    Join table between external services and the location (pandcode) and the external code for the location (externe pandcode)
    """

    location = models.ForeignKey(Location, on_delete=models.CASCADE, verbose_name="Locatie")
    external_service = models.ForeignKey(ExternalService, on_delete=models.CASCADE, verbose_name="Externe API")
    external_location_code = models.CharField(
        verbose_name="Externe locatie code", max_length=100, blank=True, null=True
    )

    class Meta:
        verbose_name = "Locatie koppeling"
        verbose_name_plural = "Locatie koppelingen"

    def __str__(self):
        return f"{self.location}, {self.external_service}, {self.external_location_code}"


class Log(models.Model):
    """
    Log model for keeping a log on system and content changes
    """

    class Action:
        """
        Action performed on the object being logged (CRUD)
        """

        CREATE = 0
        READ = 1
        UPDATE = 2
        DELETE = 3

        choices = (
            (CREATE, _("create")),
            (READ, _("read")),
            (UPDATE, _("update")),
            (DELETE, _("delete")),
        )

    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, blank=True, null=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, blank=True, null=True)
    action = models.PositiveSmallIntegerField(choices=Action.choices)
    object_name = models.CharField(verbose_name="Object", max_length=100)
    object_id = models.IntegerField(verbose_name="Id")
    field = models.CharField(max_length=100, null=True, blank=True)
    message = models.CharField(max_length=1000)

    class Meta:
        verbose_name = "Datafundament log"
        verbose_name_plural = "Datafundament logs"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.content_type.name}, {self.user}, {self.field}, {self.message}"
