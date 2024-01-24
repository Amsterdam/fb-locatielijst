from typing import Self
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from locations.validators import get_locationdata_validator
from locations.models import Location, LocationProperty, PropertyOption, LocationData, ExternalService, LocationExternalService

class LocationProcessor():
    # Switch to include all properties (including private), or only public properties
    include_private_properties = False
    
    def _add_location_data(self, location, location_property, property_option, value)-> LocationData:
        location_data = LocationData(
            location = location,
            location_property = location_property,
            property_option = property_option,
            value = value,
        )
        location_data.full_clean()

        return location_data

    def _to_location_data_list(self)-> list:
        location_data_list = []

        # Create for each location property a location data instance
        for location_property in self.location_property_instances:
            property_value = getattr(self, location_property.short_name) if getattr(self, location_property.short_name) else None

            # In case of a choice list, set the property_option attribute
            if location_property.property_type == 'CHOICE' and property_value:
                # If multiple
                if location_property.multiple:
                    if not type(property_value) == list:
                        property_value = property_value.split(',') # Leuk als dit geen komma gescheiden lijst is

                    for option in property_value:
                        property_option = PropertyOption.objects.get(location_property=location_property, option=option)
                        location_data_list.append(
                            self._add_location_data(self.location_instance, location_property, property_option, None)
                        )
                else:
                    property_option = PropertyOption.objects.get(location_property=location_property, option=property_value) 
                    location_data_list.append(
                        self._add_location_data(self.location_instance, location_property, property_option, None)
                    )
            else: 
                location_data_list.append(
                    self._add_location_data(self.location_instance, location_property, None, property_value)
                )
    
        return location_data_list

    def _set_location_properties(self)-> None:
        """
        Get location data fields from the Location model and LocationProperties 
        """
        # List to hold all location data items, starting with fields from Location
        self.location_properties = list(['pandcode', 'naam'])

        # Get all location properties and add the names to the location properties list
        # List is filtered for private accessibility
        if self.include_private_properties:
            self.location_property_instances =  [obj for obj in LocationProperty.objects.all().order_by('order', 'short_name')]
        else:
            self.location_property_instances =  [obj for obj in LocationProperty.objects.filter(public=True).order_by('order', 'short_name')]
        self.location_properties.extend([obj.short_name for obj in self.location_property_instances])

        # Get all external service links
        if self.include_private_properties:
            self.external_service_instances = [obj for obj in ExternalService.objects.all().order_by('short_name')]
        else:
            self.external_service_instances = [obj for obj in ExternalService.objects.filter(public=True).order_by('short_name')]
        self.location_properties.extend([obj.short_name for obj in self.external_service_instances])

        # Set attributes from all the available location properties
        for property in self.location_properties:
            setattr(self, property, None)

    def __init__(self, data: dict=None, include_private_properties: bool=False):
        """
        Initiate the object with all location property fields and,
        when a dict is passed, with the corresponding values
        attr: include_private_properties
          Properties are filtered on whether they are publicly or privately visible.
        Default is false; only the public properties will be set
        """
        # Set location properties access
        self.include_private_properties = include_private_properties

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
    def get(cls, pandcode: int, include_private_properties: bool=False)-> Self: 
        """
        Retrieve a location from the database and return it as an instance of this class
        """
        object = cls(include_private_properties=include_private_properties)
        object.location_instance = Location.objects.get(pandcode=pandcode) # TODO in de location_data related set zit alle data ook al is private=False

        setattr(object, 'pandcode', getattr(object.location_instance, 'pandcode'))
        setattr(object, 'naam', getattr(object.location_instance, 'name'))
        last_modified = timezone.localtime(getattr(object.location_instance, 'last_modified')).strftime('%d-%m-%Y %H:%M')
        setattr(object, 'gewijzigd', last_modified)

        # Add location properties to the object
        if object.include_private_properties:
            location_data_set = object.location_instance.locationdata_set.all()
        else:
            location_data_set = object.location_instance.locationdata_set.filter(location_property__public=True)

        for location_data in location_data_set:
            location_property = location_data.location_property
            property_option = location_data.property_option
            value = None
            if location_property.property_type == 'CHOICE' and property_option:
                if location_property.multiple:
                    current_value = getattr(object, location_property.short_name)
                    if not current_value:
                        value = list([property_option.option])
                    else:
                        current_value.append(property_option.option)
                        value = current_value
                else:
                    value = property_option.option
            else:
                value = location_data.value
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
                get_locationdata_validator(location_property, value)

    def save(self)-> Location:
        """
        Save the object as a Location model with related LocationData objects
        """
        # Validate the instance
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

            # With every save, old location_data is deleted and the (new) data is (re)added;
            # this circumvents the necessity for updating existing objects
            self.location_instance.locationdata_set.all().delete()

            # Create a list of LocationData objects
            location_data_list = self._to_location_data_list()

            # Save the location data objects
            LocationData.objects.bulk_create(location_data_list)

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