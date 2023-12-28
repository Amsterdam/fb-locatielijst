from typing import Self
from django.db import transaction
from django.forms import ValidationError
from locations.models import Location, LocationProperty, PropertyOption, LocationData, ExternalService, LocationExternalService
from locations.validators import LocationDataValidator

class LocationDataProcessor():
    location_model = None

    def _set_location_properties(self)-> None:
        """
        Get location data fields form the Location model and LocationProperties 
        """
        # Object to hold all location data items in one list
        self.location_properties_list = list()

        # Get all model fields excluding related fields or auto id's
        self.location_model_fields = [field for field in Location._meta.get_fields(include_parents=False) if field.concrete and not (
            field.is_relation or field.name == 'id')]
        self.location_property_instances =  [obj for obj in LocationProperty.objects.all()]

        # Set attributes for properties from the Location model
        for field in self.location_model_fields:
            setattr(self, field.name, None)
            self.location_properties_list.append(field.name)

        # Set attributes from all the available LocationProperties
        for location_property in self.location_property_instances:
            setattr(self, location_property.short_name, None)
            self.location_properties_list.append(location_property.short_name)

    def __init__(self, data: dict=None):
        """
        Initiate the object with all location property fields and,
        when a dict is passed, with the corresponding values
        """
        # Set the location data fields for this instance
        self._set_location_properties()

        # Set values
        if data:
            for key,value in data.items():
                if key in self.location_properties_list:
                    setattr(self, key, value)
                else:
                    raise ValidationError(f'{key} is not a valid location property')
                    

    @classmethod
    def get(cls, building_code)-> Self: 
        """
        Retrieve a location from the database and return it as an instance of this class
        """
        object = cls()
        object.location_model = Location.objects.get(building_code=building_code)
        
        for field in object.location_model_fields:
            value = getattr(object.location_model, field.name)
            setattr(object, field.name, value)

        for location_data in object.location_model.locationdata_set.all():
            if location_data.location_property.property_type == 'CHOICE':
                value = location_data.property_option.option
            else:
                value = location_data.value
            setattr(object, location_data.location_property.short_name, value)

        return object

    def get_dict(self) -> dict:
        """
        Return a dictionary of all the 'real' properties of a location  
        """
        dictionary = {attr: getattr(self, attr) for attr in self.location_properties_list}
      
        return dictionary

    def update(self):...
        
    def archive(self):...

    def validate(self):
        """
        Validate class specific properties
        """
        for location_property in self.location_property_instances:
            # Location properties that are required should have a value
            if location_property.required and not getattr(self, location_property.short_name):
                raise ValidationError(f'Value required for {location_property.label}')

    def save(self)-> Location:
        """
        Save the object as a Location model with related LocationData models
        """
        # Run validation
        self.validate()
        new_instance =  False # TODO gebruiken voor bestaande of nieuwe locatie

        # If a Location model instance has not been set yet
        if not isinstance(self.location_model, Location):
            self.location_model = Location()
            new_instance = True

        # Set the attributes for the Location model instance
        for field in self.location_model_fields:
            setattr(self.location_model, field.name, getattr(self, field.name))

        # Atomic is used to prevent incomplete locations being added;
        # for instance when a specific property value is rejected by the db
        with transaction.atomic():
            # Save the location model first before adding LocationData
            self.location_model.full_clean()
            self.location_model.save()

            # Add all the LocationData to the Location model
            for location_property in self.location_property_instances:
                value = getattr(self, location_property.short_name)

                # TODO IETS DOEN MET BESTAANDE OF NIEUWE LOCATIEDATA_SET, ANDERS KRIJG JE DUBBELE LOCATIEDATA

                if value:
                    location_data = LocationData(
                        location = self.location_model,
                        location_property = location_property,
                    )
                    if location_property.property_type == 'CHOICE':
                        location_data.property_option = PropertyOption.objects.get(location_property=location_property, option=value)
                    else: 
                        location_data.value = value
                    
                    location_data.clean()
                    location_data.save()

    def __repr__(self):
        return f'{self.building_code}, {self.name}'