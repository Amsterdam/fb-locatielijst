import unittest.mock as mock
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.test import TestCase
from locations.models import Location, LocationProperty, PropertyOption
from locations.processors import LocationDataProcessor


class TestDataLocationProcessor(TestCase):
    '''
    Test processing of location property data
    '''

    def setUp(self) -> None:
        self.boolean_property = LocationProperty.objects.create(
            short_name='occupied', label='occupied', property_type='BOOL', required=True)
        self.date_property = LocationProperty.objects.create(
            short_name='build', label='build_year', property_type='DATE', required=True)
        self.email_property = LocationProperty.objects.create(
            short_name='mail', label='mail_address', property_type='EMAIL', required=True)
        self.integer_property = LocationProperty.objects.create(
            short_name='floors', label='number_of_floors', property_type='INT', required=True)
        self.string_property = LocationProperty.objects.create(
            short_name='color', label='building_color', property_type='STR', required=True)
        self.url_property = LocationProperty.objects.create(
            short_name='url', label='web_address', property_type='URL', required=True)
        self.choice_property = LocationProperty.objects.create(
            short_name='type', label='building_type', property_type='CHOICE', required=True)
        self.choice_option = PropertyOption.objects.create(
            location_property=self.choice_property, option='Office')
        self.location_data_dict = dict({
            'building_code': '24000',
            'name': 'Amstel 1',
            'description': 'Stadhuis',
            'active': 'Ja',
            'street': 'Amstel',
            'street_number': '1',
            'postal_code': '1000 AA',
            'city': 'Amsterdam',
            'occupied': 'Ja',
            'build': '01-12-2023',
            'mail': 'mail@example.org',
            'floors': '11',
            'color': 'Yellow',
            'url': 'https://example.org',
            'type': 'Office',
        })

    def test_set_location_properties(self):
        '''
        Verify if all the expected location fields and properties are filtered
        correctly and present as attribute
        '''
        # Field which are defined in the model
        expected_location_fields = {
            'building_code',
            'name',
            'short_name',
            'description',
            'active',
            'last_modified',
            'street',
            'street_number',
            'street_number_letter',
            'street_number_extension',
            'postal_code',
            'city',
            'construction_year',
            'floor_area',
            'longitude',
            'latitude',
            'rd_x',
            'rd_y',
            'note',
        }
        # Dynamic location properties defined for this test
        expected_location_properties = {
            'occupied',
            'build',
            'mail',
            'floors',
            'color',
            'url',
            'type',
        }

        # Combined list of both types of properties
        expected_properties_combined = expected_location_fields.union(
            expected_location_properties
        )

        # Location fields and properties filtered by _set_location_properties()
        processor = LocationDataProcessor()
        found_location_fields = set([field.name for field in processor.location_model_fields])
        found_location_properties = set([instance.short_name for instance in processor.location_property_instances])
        found_properties_combined = set(processor.location_properties_list)

        # Location field sets should be equal
        self.assertEqual(expected_location_fields, found_location_fields)
        # Location property sets should be equal
        self.assertEqual(expected_location_properties, found_location_properties)
        # Combined set should be equal
        self.assertEqual(expected_properties_combined, found_properties_combined)

        # All expected fields should have an attribute in the LocationProcessorData object
        for field in expected_properties_combined:
            self.assertTrue(hasattr(processor, field), field)

    def test_init_with_data(self):
        '''
        Test if an instancve of LocationDataProcessor is created
        and if the attributes have the correct value
        '''
        location_processor = LocationDataProcessor(self.location_data_dict)
        # Verifiy the instance and the attribute values
        self.assertIsInstance(location_processor, LocationDataProcessor)
        self.assertEqual(location_processor.building_code, self.location_data_dict['building_code'])
        self.assertEqual(location_processor.name, self.location_data_dict['name'])
        self.assertEqual(location_processor.description, self.location_data_dict['description'])
        self.assertEqual(location_processor.active, self.location_data_dict['active'])
        self.assertEqual(location_processor.street, self.location_data_dict['street'])
        self.assertEqual(location_processor.street_number, self.location_data_dict['street_number'])
        self.assertEqual(location_processor.postal_code, self.location_data_dict['postal_code'])
        self.assertEqual(location_processor.city, self.location_data_dict['city'])
        self.assertEqual(location_processor.occupied, self.location_data_dict['occupied'])
        self.assertEqual(location_processor.build, self.location_data_dict['build'])
        self.assertEqual(location_processor.mail, self.location_data_dict['mail'])
        self.assertEqual(location_processor.floors, self.location_data_dict['floors'])
        self.assertEqual(location_processor.color, self.location_data_dict['color'])
        self.assertEqual(location_processor.url, self.location_data_dict['url'])
        self.assertEqual(location_processor.type, self.location_data_dict['type'])

    def test_location_save(self):
        '''
        Test if a LocationDataProcessor object can be saved in the DB
        as a Location and related LocationData
        '''
        # Check that no location exists in the database
        self.assertEqual(Location.objects.all().count(), 0)
        # Create and save a Location
        LocationDataProcessor(self.location_data_dict).save()

        # Check if the location has been added to the database
        # Only one location should exist in the database
        self.assertEqual(Location.objects.all().count(), 1)

        # Get the object
        get_location = Location.objects.get(building_code=self.location_data_dict['building_code'])

        # Check the attribute values for the Location() instance
        self.assertEqual(get_location.building_code, int(self.location_data_dict['building_code']))
        self.assertEqual(get_location.name, self.location_data_dict['name'])
        self.assertEqual(get_location.description, self.location_data_dict['description'])
        self.assertEqual(get_location.active, self.location_data_dict['active'])
        self.assertEqual(get_location.street, self.location_data_dict['street'])
        self.assertEqual(get_location.street_number, int(self.location_data_dict['street_number']))
        self.assertEqual(get_location.postal_code, self.location_data_dict['postal_code'])
        self.assertEqual(get_location.city, self.location_data_dict['city'])
        # Check the LocationData() values
        location_data = get_location.locationdata_set.all()
        self.assertEqual(location_data[0].location_property, self.boolean_property)
        self.assertEqual(location_data[0].value, self.location_data_dict['occupied'])
        self.assertEqual(location_data[1].location_property, self.date_property)
        self.assertEqual(location_data[1].value, self.location_data_dict['build'])
        self.assertEqual(location_data[2].location_property, self.email_property)
        self.assertEqual(location_data[2].value, self.location_data_dict['mail'])
        self.assertEqual(location_data[3].location_property, self.integer_property)
        self.assertEqual(location_data[3].value, self.location_data_dict['floors'])
        self.assertEqual(location_data[4].location_property, self.string_property)
        self.assertEqual(location_data[4].value, self.location_data_dict['color'])
        self.assertEqual(location_data[5].location_property, self.url_property)
        self.assertEqual(location_data[5].value, self.location_data_dict['url'])
        self.assertEqual(location_data[6].location_property, self.choice_property)
        self.assertEqual(location_data[6].property_option.option, self.location_data_dict['type'])

    def test_location_save_atomic(self):
        '''
        Test that neither a Location or LocationData will be added to the DB
        if an error occurs during save().
        '''
        # Init location with non existing building_type option
        location = LocationDataProcessor(self.location_data_dict)
        location.type = 'Tomato'
        
        # When saving the object, an ObjectDoesNotExist should be raised because Tomato is not a valid choice value
        self.assertRaises(ObjectDoesNotExist, location.save)
        # Verify that no object has been added to the database
        self.assertEqual(Location.objects.all().count(), 0)

    def test_validation(self):
        '''
        Test the validation method
        '''
        # Init a location
        location = LocationDataProcessor(self.location_data_dict)

        # Set occupied to an empty string
        location.occupied = ''
        # Verify that a validation Error occurs because occupied is an empty string
        with self.assertRaises(ValidationError) as validation_error:
            location.validate()
        # Verify the error message
        self.assertEqual(
            validation_error.exception.message,
            f'Value required for {self.boolean_property.label}',
        )

        # Set occupied to None
        location.occupied = None
        # Verify that a validation Error occurs because occupied is None
        with self.assertRaises(ValidationError) as validation_error:
            location.validate()
        # Verify the error message
        self.assertEqual(
            validation_error.exception.message,
            f'Value required for {self.boolean_property.label}',
        )

    def test_location_get(self):
        '''
        Test retrieving a locaiont data object from the database
        '''
        # First create and save an object
        LocationDataProcessor(self.location_data_dict).save()

        # Get the object
        get_location = LocationDataProcessor.get(building_code=self.location_data_dict['building_code'])

        # Verifiy the instance and the attribute values
        self.assertIsInstance(get_location, LocationDataProcessor)
        self.assertEqual(get_location.building_code, int(self.location_data_dict['building_code']))
        self.assertEqual(get_location.name, self.location_data_dict['name'])
        self.assertEqual(get_location.description, self.location_data_dict['description'])
        self.assertEqual(get_location.active, self.location_data_dict['active'])
        self.assertEqual(get_location.street, self.location_data_dict['street'])
        self.assertEqual(get_location.street_number, int(self.location_data_dict['street_number']))
        self.assertEqual(get_location.postal_code, self.location_data_dict['postal_code'])
        self.assertEqual(get_location.city, self.location_data_dict['city'])
        self.assertEqual(get_location.occupied, self.location_data_dict['occupied'])
        self.assertEqual(get_location.build, self.location_data_dict['build'])
        self.assertEqual(get_location.mail, self.location_data_dict['mail'])
        self.assertEqual(get_location.floors, self.location_data_dict['floors'])
        self.assertEqual(get_location.color, self.location_data_dict['color'])
        self.assertEqual(get_location.url, self.location_data_dict['url'])
        self.assertEqual(get_location.type, self.location_data_dict['type'])

    def test_dict_method(self):
        '''
        Test the function for returning a dictionary of the locations' attributes
        '''
        # First create and save an object
        LocationDataProcessor(self.location_data_dict).save()

        # Get dictionary of the LocationDataProcessor object
        location_dict = LocationDataProcessor.get(self.location_data_dict['building_code']).get_dict()

        # Verifiy the instance and the attribute values
        self.assertIsInstance(location_dict, dict)
        self.assertEqual(location_dict['building_code'], int(self.location_data_dict['building_code']))
        self.assertEqual(location_dict['name'], self.location_data_dict['name'])
        self.assertEqual(location_dict['description'], self.location_data_dict['description'])
        self.assertEqual(location_dict['active'], self.location_data_dict['active'])
        self.assertEqual(location_dict['street'], self.location_data_dict['street'])
        self.assertEqual(location_dict['street_number'], int(self.location_data_dict['street_number']))
        self.assertEqual(location_dict['postal_code'], self.location_data_dict['postal_code'])
        self.assertEqual(location_dict['city'], self.location_data_dict['city'])
        self.assertEqual(location_dict['occupied'], self.location_data_dict['occupied'])
        self.assertEqual(location_dict['build'], self.location_data_dict['build'])
        self.assertEqual(location_dict['mail'], self.location_data_dict['mail'])
        self.assertEqual(location_dict['floors'], self.location_data_dict['floors'])
        self.assertEqual(location_dict['color'], self.location_data_dict['color'])
        self.assertEqual(location_dict['url'], self.location_data_dict['url'])
        self.assertEqual(location_dict['type'], self.location_data_dict['type'])
