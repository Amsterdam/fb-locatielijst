from typing import Self
from django.db import transaction
from django.forms import ValidationError
from django.utils import timezone
from locations.models import Location, LocationProperty, PropertyOption, LocationData, ExternalService, LocationExternalService

class LocationDataProcessor():
    location_instance = None
    pandcode = None
    mut_datum = None

    def _set_location_properties(self)-> None:
        """
        Get location data fields from the Location model and LocationProperties 
        """
        # List to hold all location data items, starting with fields from Location
        self.location_properties = list(['pandcode', 'naam', 'mut_datum'])

        # Get all location properties and add the names to the location properties list
        self.location_property_instances =  [obj for obj in LocationProperty.objects.all()]
        self.location_properties.extend([obj.short_name for obj in self.location_property_instances])

        # Set attributes from all the available location properties
        for property in self.location_properties:
            setattr(self, property, None)

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
                if key in self.location_properties:
                    setattr(self, key, value)
                else:
                    raise ValidationError(f'{key} is een niet bestaande locatie eigenschap')
                    

    @classmethod
    def get(cls, pandcode)-> Self: 
        """
        Retrieve a location from the database and return it as an instance of this class
        """
        object = cls()
        object.location_instance = Location.objects.get(pandcode=pandcode)

        setattr(object, 'pandcode', getattr(object.location_instance, 'pandcode'))
        setattr(object, 'naam', getattr(object.location_instance, 'naam'))
        mut_datum = timezone.localtime(getattr(object.location_instance, 'mut_datum')).strftime('%d-%m-%Y %H:%M')
        setattr(object, 'mut_datum', mut_datum)
        
        for location_data in object.location_instance.locationdata_set.all():
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
        dictionary = {attr: getattr(self, attr) for attr in self.location_properties}
      
        return dictionary

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
        Save the object as a Location model with related LocationData objects
        """
        # Run validation
        self.validate()
        
        # update or new
        update = False
        
        # If a Location model instance has not been set yet
        if not isinstance(self.location_instance, Location):
            if Location.objects.filter(pandcode=self.pandcode).exists():
                update = True
                self.location_instance = Location.objects.get(pandcode=self.pandcode)
            else:
                self.location_instance = Location()

        # Set the attributes for the Location model instance
        setattr(self.location_instance, 'naam', getattr(self, 'naam'))

        # Atomic is used to prevent incomplete locations being added;
        # for instance when a specific property value is rejected by the db
        with transaction.atomic():
            # Save the location model first before adding LocationData
            
            # TODO, can ook get_or_create gebruiken, maar dan gaat het fout met full_clean?
            
            self.location_instance.full_clean()
            self.location_instance.save()          

            # Add all the LocationData to the Location object
            for location_property in self.location_property_instances:
                value = getattr(self, location_property.short_name)

                if value:
                    location_data = LocationData(
                        location = self.location_instance,
                        location_property = location_property,
                    )
                    # In case of a choice list, set the property_option attribute
                    if location_property.property_type == 'CHOICE':
                        location_data.property_option = PropertyOption.objects.get(location_property=location_property, option=value)
                    else: 
                        location_data.value = value
                    
                    location_data.clean()
                    #location_data.save()
                    # TODO update_or_create gemaakt, maar misschien een beetje clunky nog
                    # TODO en validatie gaat nu fout omdat bij een update het nog niet bekent is of het object geupdate of nieuw is
                    defaults = {}
                    if location_property.property_type == 'CHOICE':
                        defaults['property_option'] = PropertyOption.objects.get(location_property=location_property, option=value)
                    else: 
                        defaults['value'] = value
                    obj, created = LocationData.objects.update_or_create(
                        location = self.location_instance,
                        location_property = location_property,
                        defaults = defaults
                    )

                    # Update datum mutatie?
                    self.location_instance.save()

        # TODO update pandcode wanneer het een nieuwe locatie betreft
        if not update:
            self.pandcode = self.location_instance.pandcode


    def __repr__(self):
        return f'{self.pandcode}, {self.naam}'