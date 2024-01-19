from typing import Self
from django.db import transaction
from django.forms import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from locations.validators import LocationDataValidator
from locations.models import Location, LocationProperty, PropertyOption, LocationData, ExternalService, LocationExternalService

class LocationProcessor():
    private = False

    def _set_location_properties(self)-> None:
        """
        Get location data fields from the Location model and LocationProperties 
        """
        # List to hold all location data items, starting with fields from Location
        self.location_properties = list(['pandcode', 'naam'])

        # Get all location properties and add the names to the location properties list
        # List is filtered for private accessibility
        if self.private:
            self.location_property_instances =  [obj for obj in LocationProperty.objects.all().order_by('order', 'short_name')]
        else:
            self.location_property_instances =  [obj for obj in LocationProperty.objects.filter(public=True).order_by('order', 'short_name')]
        self.location_properties.extend([obj.short_name for obj in self.location_property_instances])

        # Get all external service links
        if self.private:
            self.external_service_instances = [obj for obj in ExternalService.objects.all().order_by('short_name')]
        else:
            self.external_service_instances = [obj for obj in ExternalService.objects.filter(public=True).order_by('short_name')]
        self.location_properties.extend([obj.short_name for obj in self.external_service_instances])

        # Set attributes from all the available location properties
        for property in self.location_properties:
            setattr(self, property, None)

    def __init__(self, data: dict=None, private: bool=False):
        """
        Initiate the object with all location property fields and,
        when a dict is passed, with the corresponding values
        attr: Private
          Properties are filtered on whether they are publicly or privately visible.
        Default is false; only the public properties will be set
        """
        # Set location properties access
        self.private = private

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
    def get(cls, pandcode: int, private: bool=False)-> Self: 
        """
        Retrieve a location from the database and return it as an instance of this class
        """
        object = cls(private=private)
        object.location_instance = Location.objects.get(pandcode=pandcode)

        setattr(object, 'pandcode', getattr(object.location_instance, 'pandcode'))
        setattr(object, 'naam', getattr(object.location_instance, 'name'))
        last_modified = timezone.localtime(getattr(object.location_instance, 'last_modified')).strftime('%d-%m-%Y %H:%M')
        setattr(object, 'gewijzigd', last_modified)
        
        # Add location properties to the object
        for location_data in object.location_instance.locationdata_set.all():
            if location_data.location_property.property_type == 'CHOICE' and getattr(location_data, 'property_option'):
                value = location_data.property_option.option
            else:
                value = location_data.value
            setattr(object, location_data.location_property.short_name, value)

        # Add location properties to the object
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
        dictionary['gewijzigd'] = getattr(self, 'gewijzigd', None)

        return dictionary

    def validate(self):
        """
        Validate class specific properties
        """
        for location_property in self.location_property_instances:
            # Validate the value of every location property
            value = getattr(self, location_property.short_name)
            if value:
                LocationDataValidator.validate(location_property, value)

    def save(self)-> Location:
        """
        Save the object as a Location model with related LocationData objects
        """
        # Run validation
        self.validate()
     
        # If a Location model instance has not been set yet
        if Location.objects.filter(pandcode=self.pandcode).exists():
            self.location_instance = Location.objects.get(pandcode=self.pandcode)
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

         # Atomic is used to prevent incomplete locations being added;
        # for instance when a specific property value is rejected by the db
        with transaction.atomic():
            # Save the location model first before adding LocationData
            self.location_instance.full_clean()
            self.location_instance.save()

            # Add all the LocationData to the Location object
            for location_property in self.location_property_instances:
                # Check if the location_data already exists; otherwise create new instance
                if self.location_instance.locationdata_set.filter(location=self.location_instance, location_property=location_property).exists():
                    location_data = self.location_instance.locationdata_set.get(location=self.location_instance, location_property=location_property)
                else:
                    location_data = LocationData(location = self.location_instance, location_property = location_property)

                if getattr(self, location_property.short_name):
                    value = getattr(self, location_property.short_name)
                else:
                    value = None
                # In case of a choice list, set the property_option attribute
                if location_property.property_type == 'CHOICE' and value:
                    location_data.property_option = PropertyOption.objects.get(location_property=location_property, option=value)
                else: 
                    location_data.value = value

                # Clean the data                    
                location_data.full_clean()

                # Save the instance
                location_data.save()

            # Add external service data tot the Location object
            for service in self.external_service_instances:
                if getattr(self, service.short_name):
                    value = getattr(self, service.short_name)
                else:
                    value = None
                
                # Check if an external service instance exists; otherwise create a new instance
                if self.location_instance.locationexternalservice_set.filter(location=self.location_instance, external_service=service).exists():
                    location_external = self.location_instance.locationexternalservice_set.get(location=self.location_instance, external_service=service)
                else:
                    location_external = LocationExternalService(location = self.location_instance, external_service = service)

                # Set the external service code and save the instance
                location_external.external_location_code = value
                location_external.full_clean()
                location_external.save()

    def __repr__(self):
        return f'{self.pandcode}, {self.naam}'