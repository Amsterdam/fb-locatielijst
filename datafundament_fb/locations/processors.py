from typing import Self
from django.db import transaction
from django.forms import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from locations.models import Location, LocationProperty, PropertyOption, LocationData, ExternalService, LocationExternalService

class LocationProcessor():
    location_instance = None

    def _set_location_properties(self)-> None:
        """
        Get location data fields from the Location model and LocationProperties 
        """
        # List to hold all location data items, starting with fields from Location
        self.location_properties = list(['pandcode', 'naam'])

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

    @classmethod
    def get(cls, pandcode)-> Self: 
        """
        Retrieve a location from the database and return it as an instance of this class
        """
        object = cls()
        object.location_instance = Location.objects.get(pandcode=pandcode)

        setattr(object, 'pandcode', getattr(object.location_instance, 'pandcode'))
        setattr(object, 'naam', getattr(object.location_instance, 'name'))
        last_modified = timezone.localtime(getattr(object.location_instance, 'last_modified')).strftime('%d-%m-%Y %H:%M')
        setattr(object, 'gewijzigd', last_modified)
        
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
        # Add last_modified date to the dictionary
        if getattr(self, 'gewijzigd'):
            dictionary['gewijzigd'] = self.gewijzigd

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

        # If a Location model instance has not been set yet
        if not isinstance(self.location_instance, Location):
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
            # TODO, kan ook get_or_create gebruiken, maar dan gaat het fout met full_clean?
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
                        # TODO als een optie niet bestaat, dan moet dit afgevangen worden... dit is eigenlijk daarvoor niet de plaats
                        # OPTIE: voeg de optie meteen toe als deze niet bestaat
                        if PropertyOption.objects.filter(location_property=location_property, option=value).exists():
                            location_data.property_option = PropertyOption.objects.get(location_property=location_property, option=value)
                        else:
                            option = PropertyOption(location_property=location_property, option=value)
                            option.full_clean()
                            option.save()
                            location_data.property_option = option
                    else: 
                        location_data.value = value
                    
                    location_data.clean()
                    #location_data.save()
                    # TODO update_or_create gemaakt, maar misschien een beetje clunky nog
                    # TODO en single validatie gaat nu fout omdat bij een update het nog niet bekent is of het object geupdate of nieuw is
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

    def __repr__(self):
        return f'{self.pandcode}, {self.naam}'