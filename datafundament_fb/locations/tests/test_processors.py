import unittest.mock as mock
from django.core.exceptions import ValidationError
from django.test import TestCase
from locations.models import Location, LocationProperty, PropertyOption
from locations.processors import LocationProcessor


class TestLocationProcessor(TestCase):
    '''
    Test processing of location property data
    '''

    def setUp(self) -> None:
        self.boolean_property = LocationProperty.objects.create(
            short_name='occupied', label='occupied', property_type='BOOL', required=True, public=True)
        self.date_property = LocationProperty.objects.create(
            short_name='build', label='build_year', property_type='DATE', required=True, public=True)
        self.email_property = LocationProperty.objects.create(
            short_name='mail', label='mail_address', property_type='EMAIL', required=True)
        self.integer_property = LocationProperty.objects.create(
            short_name='floors', label='number_of_floors', property_type='INT', required=True)
        self.memo_property = LocationProperty.objects.create(
            short_name='note', label='note', property_type='MEMO', required=True)
        self.postal_code_property = LocationProperty.objects.create(
            short_name='postcode', label='postal_code', property_type='POST', required=True)
        self.string_property = LocationProperty.objects.create(
            short_name='color', label='building_color', property_type='STR')
        self.url_property = LocationProperty.objects.create(
            short_name='url', label='web_address', property_type='URL')
        self.choice_property = LocationProperty.objects.create(
            short_name='type', label='building_type', property_type='CHOICE', required=True)
        self.choice_option = PropertyOption.objects.create(
            location_property=self.choice_property, option='Office')
        self.location_data_dict = dict({
            'pandcode': '24000',
            'naam': 'Stopera',
            'occupied': 'Ja',
            'build': '01-12-2023',
            'mail': 'mail@example.org',
            'note': 'Notitie',
            'postcode': '1000 AA',
            'floors': '11',
            'color': 'Yellow',
            'url': 'https://example.org',
            'type': 'Office',
        })

    def test_set_location_properties_public(self):
        '''
        Verify if all the expected location fields and properties are filtered
        correctly and present as attribute. Only publicly visible properties should be included.
        '''

        # Dynamic location properties defined for this test
        expected_location_properties = {
            'pandcode',
            'naam',
            'occupied',
            'build',
        }

        # Location fields and properties filtered by _set_location_properties(); added with fields from location
        # Included properties are public
        processor = LocationProcessor()
        location_properties = processor.location_properties
        found_location_properties = set(location_properties)

        # Location property sets should be equal
        self.assertEqual(expected_location_properties, found_location_properties)

        # All expected fields should have an attribute in the LocationProcessorData object
        for field in expected_location_properties:
            self.assertTrue(hasattr(processor, field), field)

    def test_set_location_properties_private(self):
        '''
        Verify if all the expected location fields and properties are filtered
        correctly and present as attribute. All properties (private and public) should be included.
        '''

        # Dynamic location properties defined for this test
        expected_location_properties = {
            'pandcode',
            'naam',
            'occupied',
            'build',
            'mail',
            'floors',
            'note',
            'postcode',
            'color',
            'url',
            'type',
        }

        # Location fields and properties filtered by _set_location_properties(); added with fields from location
        # Included properties are private and public
        processor = LocationProcessor(private=True)
        location_properties = processor.location_properties
        found_location_properties = set(location_properties)

        # Location property sets should be equal
        self.assertEqual(expected_location_properties, found_location_properties)

        # All expected fields should have an attribute in the LocationProcessorData object
        for field in expected_location_properties:
            self.assertTrue(hasattr(processor, field), field)

    def test_init_with_data(self):
        '''
        Test if an instancve of LocationProcessor is created
        and if the attributes have the correct value
        '''
        location_processor = LocationProcessor(private=True, data=self.location_data_dict)

        # Verifiy the instance and the attribute values
        self.assertIsInstance(location_processor, LocationProcessor)
        self.assertEqual(location_processor.pandcode, self.location_data_dict['pandcode'])
        self.assertEqual(location_processor.occupied, self.location_data_dict['occupied'])
        self.assertEqual(location_processor.build, self.location_data_dict['build'])
        self.assertEqual(location_processor.mail, self.location_data_dict['mail'])
        self.assertEqual(location_processor.floors, self.location_data_dict['floors'])
        self.assertEqual(location_processor.note, self.location_data_dict['note'])
        self.assertEqual(location_processor.postcode, self.location_data_dict['postcode'])
        self.assertEqual(location_processor.color, self.location_data_dict['color'])
        self.assertEqual(location_processor.url, self.location_data_dict['url'])
        self.assertEqual(location_processor.type, self.location_data_dict['type'])

    def test_location_save(self):
        '''
        Test if a LocationProcessor object can be saved in the DB
        as a Location and related LocationData
        '''
        # Check that no location exists in the database
        self.assertEqual(Location.objects.all().count(), 0)
        # Create and save a Location
        LocationProcessor(private=True, data=self.location_data_dict).save()

        # Check if the location has been added to the database
        # Only one location should exist in the database
        self.assertEqual(Location.objects.all().count(), 1)

        # Get the object
        get_location = Location.objects.get(pandcode=self.location_data_dict['pandcode'])

        # Check the attribute values for the Location() instance
        self.assertEqual(get_location.pandcode, int(self.location_data_dict['pandcode']))
        self.assertEqual(get_location.name, self.location_data_dict['naam'])

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
        self.assertEqual(location_data[4].location_property, self.memo_property)
        self.assertEqual(location_data[4].value, self.location_data_dict['note'])
        self.assertEqual(location_data[5].location_property, self.postal_code_property)
        self.assertEqual(location_data[5].value, self.location_data_dict['postcode'])
        self.assertEqual(location_data[6].location_property, self.string_property)
        self.assertEqual(location_data[6].value, self.location_data_dict['color'])
        self.assertEqual(location_data[7].location_property, self.url_property)
        self.assertEqual(location_data[7].value, self.location_data_dict['url'])
        self.assertEqual(location_data[8].location_property, self.choice_property)
        self.assertEqual(location_data[8].property_option.option, self.location_data_dict['type'])

    @mock.patch('locations.validators.LocationDataValidator.valid_url')
    def test_location_save_atomic(self, mock):
        '''
        Test that neither a Location or LocationData will be added to the DB
        if an error occurs during save().
        '''
        # Init location with an invalid attribute type 
        location = LocationProcessor(self.location_data_dict, private=True)

        # Mock the validation() so an error is raised
        mock.side_effect = (ValueError)
        
        # When saving the object, an ObjectDoesNotExist should be raised because Tomato is not a valid choice value
        with self.assertRaises(ValueError) as validation_error:
            location.save()

        # Verify that no object has been added to the database
        self.assertEqual(Location.objects.all().count(), 0)


    def test_invalid_choice_value(self):
        '''
        Test that an invalid choice value for a Location Property() during save results in a validation error.
        '''
        # Init location with non existing type option
        location = LocationProcessor(private=True, data=self.location_data_dict)
        location.type = 'Tomato'
        
        # When saving the object, a ValidationError should be raised because Tomato is not a valid choice value
        with self.assertRaises(ValidationError) as validation_error:
            location.save()

        # Verify the error message
        self.assertEqual(
            validation_error.exception.message,
            f"'Tomato' is not a valid choice for {self.choice_property.label}"
        )

    def test_location_save_with_empty_value(self):
        # Test whether a previously filled value will be emptied
        LocationProcessor(self.location_data_dict, private=True).save()

        # Get the location and delete a property value
        location = LocationProcessor.get(pandcode=self.location_data_dict['pandcode'], private=True)
        location.url = None
        location.save()

        # Verify that the location properties have no value in the db
        location = LocationProcessor.get(pandcode=self.location_data_dict['pandcode'], private=True)
        self.assertEqual(location.url, None)

    def test_validation(self):
        '''
        Test the validation method
        '''
        # Init a location
        location = LocationProcessor(private=True, data=self.location_data_dict)

        # Set occupied to an empty string
        location.occupied = 'Misschien'
        # Verify that a validation Error occurs because occupied is an empty string
        with self.assertRaises(ValidationError) as validation_error:
            location.validate()
        # Verify the error message
        self.assertEqual(
            validation_error.exception.message,
            f"'Misschien' is not a valid boolean",
        )

    def test_location_get(self):
        '''
        Test retrieving a locaiont data object from the database
        '''
        # First create and save an object
        LocationProcessor(private=True, data=self.location_data_dict).save()

        # Get the object
        get_location = LocationProcessor.get(pandcode=self.location_data_dict['pandcode'], private=True)

        # Verifiy the instance and the attribute values
        self.assertIsInstance(get_location, LocationProcessor)
        self.assertEqual(get_location.pandcode, int(self.location_data_dict['pandcode']))
        self.assertEqual(get_location.naam, self.location_data_dict['naam'])
        self.assertEqual(get_location.occupied, self.location_data_dict['occupied'])
        self.assertEqual(get_location.build, self.location_data_dict['build'])
        self.assertEqual(get_location.mail, self.location_data_dict['mail'])
        self.assertEqual(get_location.floors, self.location_data_dict['floors'])
        self.assertEqual(get_location.note, self.location_data_dict['note'])
        self.assertEqual(get_location.postcode, self.location_data_dict['postcode'])
        self.assertEqual(get_location.color, self.location_data_dict['color'])
        self.assertEqual(get_location.url, self.location_data_dict['url'])
        self.assertEqual(get_location.type, self.location_data_dict['type'])
        # Verify is attribute 'gewijzigd' is filled
        self.assertIsNotNone(get_location.gewijzigd)

    def test_dict_method(self):
        '''
        Test the function for returning a dictionary of the locations' attributes
        '''
        # First create and save an object
        LocationProcessor(private=True, data=self.location_data_dict).save()

        # Get dictionary of the LocationProcessor object
        location_dict = LocationProcessor.get(self.location_data_dict['pandcode'], private=True).get_dict()

        # Verifiy the instance and the attribute values
        self.assertIsInstance(location_dict, dict)
        self.assertEqual(location_dict['pandcode'], int(self.location_data_dict['pandcode']))
        self.assertEqual(location_dict['naam'], self.location_data_dict['naam'])
        self.assertEqual(location_dict['occupied'], self.location_data_dict['occupied'])
        self.assertEqual(location_dict['build'], self.location_data_dict['build'])
        self.assertEqual(location_dict['mail'], self.location_data_dict['mail'])
        self.assertEqual(location_dict['floors'], self.location_data_dict['floors'])
        self.assertEqual(location_dict['note'], self.location_data_dict['note'])
        self.assertEqual(location_dict['postcode'], self.location_data_dict['postcode'])
        self.assertEqual(location_dict['color'], self.location_data_dict['color'])
        self.assertEqual(location_dict['url'], self.location_data_dict['url'])
        self.assertEqual(location_dict['type'], self.location_data_dict['type'])
        # Verify is attribute 'gewijzigd' is filled
        self.assertIsNotNone(location_dict['gewijzigd'])