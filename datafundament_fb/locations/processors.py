from typing import Self
from django.contrib.auth.models import User, AnonymousUser
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from locations.validators import get_locationdata_validator
from locations.models import Location, LocationProperty, PropertyOption, LocationData, ExternalService, LocationExternalService

class LocationProcessor():
    # Switch to include all properties (including private), or only public properties
    user = AnonymousUser()

    def _save_location_data(self, location_property, value):
        """Helper function to create or update a LocationData instance"""

        # If a location_property has multiple, new values must be added and old ones deleted 
        if location_property.multiple:
            if value:
                values = value
            else:
                values = []
            # Cast values to list      
            if not type(values) == list:
                values = values.split(',') # Could be a thingy when the list is not comma seperated
            # Create multiple LocationData objects
            for value in values:
                if not LocationData.objects.filter(location=self.location_instance, location_property=location_property, _property_option__option=value):
                    location_data = LocationData(
                        location = self.location_instance,
                        location_property = location_property,
                        last_modified_by = self.user
                    )
                    # Set the value, clean and save the instance
                    location_data.value = value
                    location_data.full_clean()
                    location_data.save()
            # Delete multiples not in the values list
            self.location_instance.locationdata_set.filter(Q(location_property=location_property),~Q(_property_option__option__in=values)).delete()
        else:
            location_data, created = LocationData.objects.get_or_create(
                location = self.location_instance,
                location_property = location_property,
                last_modified_by = self.user
            )
            # Set the value, clean and save the instance
            location_data.value = value
            location_data.full_clean()
            location_data.save()
            
    def _set_location_properties(self)-> None:
        """
        Get location data fields from the Location model and LocationProperties 
        """
        # List to hold all location data items, starting with fields from Location
        self.location_properties = list(['pandcode', 'naam'])

        # Get all location properties and add the names to the location properties list
        # Location properties without a 'group' value be put last beforte being sorted on 'order'
        self.location_property_instances = LocationProperty.objects.all().order_by(F('group__order').asc(nulls_last=True), 'order')
        # List is filtered for private accessibility
        if not self.user.is_authenticated:
            self.location_property_instances =  self.location_property_instances.filter(public=True)
        self.location_properties.extend([obj.short_name for obj in self.location_property_instances])

        # Get all external service links
        self.external_service_instances = ExternalService.objects.all().order_by('order')
        if not self.user.is_authenticated:
            self.external_service_instances = self.external_service_instances.filter(public=True)
        self.location_properties.extend([obj.short_name for obj in self.external_service_instances])

        # Set attributes from all the available location properties
        for property in self.location_properties:
            setattr(self, property, None)

    def __init__(self, user: User=AnonymousUser(), data: dict=None):
        """
        Initiate the object with all location property fields and,
        when a dict is passed, with the corresponding values
        attr: user
          Properties are filtered on whether a user has permission.
          Default is an anonymous user
        """
        # Set User
        self.user = user
    
        # Set an empty Location instance
        self.location_instance = Location()

        # Set the location data fields for this instance
        self._set_location_properties()

        # Set values
        if data:
            for key,value in data.items():
                if key in self.location_properties:
                    setattr(self, key, value)

    @classmethod
    def get(cls, pandcode: int, user: User=AnonymousUser())-> Self: 
        """
        Retrieve a location from the database and return it as an instance of this class
        """
        object = cls(user=user)
        object.location_instance = Location.objects.get(pandcode=pandcode) # TODO in de location_data related set zit alle data ook al is private=False

        setattr(object, 'pandcode', getattr(object.location_instance, 'pandcode'))
        setattr(object, 'naam', getattr(object.location_instance, 'name'))
        created_at = timezone.localtime(getattr(object.location_instance, 'created_at')).strftime('%d-%m-%Y')
        setattr(object, 'aangemaakt', created_at)
        last_modified = timezone.localtime(getattr(object.location_instance, 'last_modified')).strftime('%d-%m-%Y %H:%M')
        setattr(object, 'gewijzigd', last_modified)
        setattr(object, 'archief', getattr(object.location_instance, 'is_archived'))

        # Add location properties to the object; filter to include non-public properties
        if object.user.is_authenticated:
            location_data_set = object.location_instance.locationdata_set.all()
        else:
            location_data_set = object.location_instance.locationdata_set.filter(location_property__public=True)

        # Set the value from the LocationData as attribute in the object instance
        for location_data in location_data_set:
            location_property = location_data.location_property
            value = None

            # Get value for multiple location data
            if location_property.multiple:
                # Check if a value has already been set
                current_value = getattr(object, location_property.short_name)
                if not current_value:
                    value = list([location_data.value])
                else:
                    current_value.append(location_data.value)
                    value = current_value
            else:
                value = location_data.value
            
            # Set the attribute value
            setattr(object, location_property.short_name, value)

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
        dictionary['aangemaakt'] = getattr(self, 'aangemaakt', None)
        dictionary['gewijzigd'] = getattr(self, 'gewijzigd', None)
        dictionary['archief'] = getattr(self, 'archief', None)

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

    def save(self)-> Location:
        """
        Save the object as a Location model with related LocationData objects
        """
        # Validate the instance
        self.validate()

        # If a Location model instance has not been set yet
        if location_instance := Location.objects.filter(pandcode=self.pandcode).first():
            self.location_instance = location_instance
            # Update the attributes for the Location model instance
            setattr(self.location_instance, 'name', getattr(self, 'naam'))
        else:
            # When importing locations, pandcode exists
            if getattr(self, 'pandcode'):
                self.location_instance = Location(pandcode=self.pandcode, name=self.naam)
            else:
                self.location_instance = Location(name=self.naam)
                # Update this instance with the pandcode
                self.pandcode = self.location_instance.pandcode

        self.location_instance.last_modified_by = self.user

        # Atomic is used to prevent incomplete locations being added;
        # for instance when a specific property value is rejected by the db
        with transaction.atomic():
            # Save the location model first before adding LocationData
            self.location_instance.full_clean()
            self.location_instance.save()

            # Create for each location property a locationData instance
            for location_property in self.location_property_instances:
                value = getattr(self, location_property.short_name) if getattr(self, location_property.short_name) else None
                self._save_location_data(location_property, value)

            # Add external service data tot the Location object
            for service in self.external_service_instances:
                value = getattr(self, service.short_name) if getattr(self, service.short_name) else None
                
                external_service, create = LocationExternalService.objects.get_or_create(
                    location=self.location_instance, external_service=service, last_modified_by = self.user
                )
                # Set the external service code, clean and save the instance
                external_service.external_location_code = value
                external_service.full_clean()
                external_service.save()

    def __repr__(self):
        return f'{self.pandcode}, {self.naam}'