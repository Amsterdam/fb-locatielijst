from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from typing_extensions import Self

from locations.models import (
    ExternalService,
    Location,
    LocationData,
    LocationExternalService,
    LocationProperty,
)
from locations.validators import get_locationdata_validator
from shared.context import current_user


class LocationProcessor:

    def _create_or_update(self, location_property, value):
        """Helper function to create or update a LocationData instance"""
        if location_property.multiple:
            location_data = LocationData.objects.filter(
                location=self.location_instance, location_property=location_property, _property_option__option=value
            ).first()
        else:
            location_data = LocationData.objects.filter(
                location=self.location_instance, location_property=location_property
            ).first()

        if not location_data:
            location_data = LocationData(location=self.location_instance, location_property=location_property)
        if location_data.value != value:
            location_data.value = value
            location_data.full_clean()
            location_data.save()

    def _save_location_data(self, location_property, value):
        """Helper function to save location_processor attributes"""
        # If a location_property has multiple=true, new values must be added and old ones deleted
        if location_property.multiple:
            if values := value:
                # Cast values to list
                if not type(values) == list:
                    values = values.split("|")
            else:
                values = []

            # Create multiple LocationData objects
            for value in values:
                self._create_or_update(location_property, value)

            # Delete multiples not in the values list
            self.location_instance.locationdata_set.filter(
                Q(location_property=location_property), ~Q(_property_option__option__in=values)
            ).delete()
        else:
            self._create_or_update(location_property, value)

    def _save_location_external_service(self, external_service, value):
        location_external_service = LocationExternalService.objects.filter(
            location=self.location_instance, external_service=external_service
        ).first()
        if not location_external_service:
            location_external_service = LocationExternalService(
                location=self.location_instance, external_service=external_service
            )
        if location_external_service.external_location_code != value:
            location_external_service.external_location_code = value
            location_external_service.full_clean()
            location_external_service.save()

    def _set_location_properties(self) -> None:
        """
        Get location data fields from the Location model and LocationProperties
        """
        # List to hold all location data items, starting with fields from Location
        self.location_properties = list(["pandcode", "naam"])

        # Get all location properties and add the names to the location properties list
        # List is filtered for non staff members
        self.location_property_instances = LocationProperty.objects.all()
        if not self.user.is_staff:
            self.location_property_instances = self.location_property_instances.filter(public=True)
        self.location_properties.extend([obj.short_name for obj in self.location_property_instances])

        # Get all external service links
        # List is filtered for non staff members
        self.external_service_instances = ExternalService.objects.all()
        if not self.user.is_staff:
            self.external_service_instances = self.external_service_instances.filter(public=True)
        self.location_properties.extend([obj.short_name for obj in self.external_service_instances])

        # Set attributes from all the available location properties
        for property in self.location_properties:
            setattr(self, property, None)

    def __init__(self, data: dict = None):
        """
        Initiate the object with all location property fields and,
        when a dict is passed, with the corresponding values
        """
        # User is retrieved form request by middlewhere, if none default to Anonymous
        self.user = current_user.get() or AnonymousUser

        # Set an empty Location instance
        self.location_instance = Location()

        # Set the location data fields for this instance
        self._set_location_properties()

        # Set values
        if data:
            for key, value in data.items():
                if key in self.location_properties:
                    setattr(self, key, value)

    @classmethod
    def get(cls, pandcode: int) -> Self:
        """
        Retrieve a location from the database and return it as an instance of this class
        """
        location = Location.objects.get(
            pandcode=pandcode
        )  # TODO in de location_data related set zit alle data ook al is private=False

        return cls.format_location(location)

    @classmethod
    def get_export_data(cls, pandcodes: list) -> dict:
        """
        Retrieve a list of locations from the database and return it as a dict
        """
        # Retrieve all locations in list and prefetch related locationdata
        locations = Location.objects.filter(pandcode__in=pandcodes).prefetch_related("locationdata_set")
        location_list = list()
        for location in locations:
            object = cls.format_location(location)
            # Replace list values with | seperated string for multiple choice location properties
            object_dict = object.get_dict()
            for key, value in object_dict.items():
                if type(value) == list:
                    object_dict[key] = "|".join(value)
            location_list.append(object_dict)
        return location_list

    @classmethod
    def format_location(cls, location) -> object:
        object = cls()
        object.location_instance = location
        setattr(object, "pandcode", getattr(object.location_instance, "pandcode"))
        setattr(object, "naam", getattr(object.location_instance, "name"))
        created_at = timezone.localtime(getattr(object.location_instance, "created_at")).strftime("%d-%m-%Y")
        setattr(object, "aangemaakt", created_at)
        last_modified = timezone.localtime(getattr(object.location_instance, "last_modified")).strftime(
            "%d-%m-%Y %H:%M"
        )
        setattr(object, "gewijzigd", last_modified)
        setattr(object, "archief", getattr(object.location_instance, "is_archived"))
        # Add location properties to the object; filter to include non-public properties
        if object.user.is_staff:
            location_data_set = object.location_instance.locationdata_set.all()
        else:
            location_data_set = object.location_instance.locationdata_set.filter(location_property__public=True)

        # Set the value from the LocationData as attribute in the object instance
        for location_data in location_data_set:
            value = None
            # Get value for multiple location data
            if location_data.location_property.multiple:
                # Check if a value has already been set
                current_value = getattr(object, location_data.location_property.short_name)
                if not current_value:
                    value = list([location_data.value])
                else:
                    current_value.append(location_data.value)
                    value = current_value
            else:
                value = location_data.value

            # Set the attribute value
            setattr(object, location_data.location_property.short_name, value)
        # Add external services to the object
        for service in object.location_instance.locationexternalservice_set.all():
            value = service.external_location_code
            setattr(object, service.external_service.short_name, value)

        return object

    def get_dict(self) -> dict:
        """
        Return a dictionary of all the 'real' properties of a location
        """
        dictionary = {attr: getattr(self, attr) for attr in self.location_properties}

        # Add last_modified date to the dictionary
        dictionary["aangemaakt"] = getattr(self, "aangemaakt", None)
        dictionary["gewijzigd"] = getattr(self, "gewijzigd", None)
        dictionary["archief"] = getattr(self, "archief", None)

        return dictionary

    def validate(self):
        """
        Validate class specific properties
        """
        validation_errors = []

        for location_property in self.location_property_instances:
            # Validate the value of every location property
            value = getattr(self, location_property.short_name)
            if value:
                try:
                    get_locationdata_validator(location_property, value)
                except ValidationError as validation_error:
                    validation_errors.append(validation_error)

        if validation_errors:
            raise ValidationError([validation_errors])

    def save(self) -> Location:
        """
        Save the object as a Location model with related LocationData objects
        """
        # Validate the instance
        self.validate()

        # If a Location model instance has not been set yet
        if location_instance := Location.objects.filter(pandcode=self.pandcode).first():
            self.location_instance = location_instance
            # Update the attributes for the Location model instance
            setattr(self.location_instance, "name", getattr(self, "naam"))
        else:
            # When importing locations, pandcode exists
            if getattr(self, "pandcode"):
                self.location_instance = Location(pandcode=self.pandcode, name=self.naam)
            else:
                self.location_instance = Location(name=self.naam)
                # Update this instance with the pandcode
                self.pandcode = self.location_instance.pandcode

        # Atomic is used to prevent incomplete locations being added;
        # for instance when a specific property value is rejected by the db
        with transaction.atomic():
            # Save the location model first before adding LocationData
            self.location_instance.full_clean()
            self.location_instance.save()

            # Create for each location property a locationData instance
            for location_property in self.location_property_instances:
                value = (
                    getattr(self, location_property.short_name) if getattr(self, location_property.short_name) else None
                )
                self._save_location_data(location_property, value)

            # Add external service data tot the Location object
            for external_service in self.external_service_instances:
                value = (
                    getattr(self, external_service.short_name) if getattr(self, external_service.short_name) else None
                )
                self._save_location_external_service(external_service, value)

    def __repr__(self):
        return f"{self.pandcode}, {self.naam}"
