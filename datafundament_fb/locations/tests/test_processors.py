import  unittest.mock as mock
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.test import TestCase
from locations.models import Location, LocationProperty, PropertyOption
from locations.processors import LocationDataProcessor

class TestDataLocationProcessor(TestCase):
    """
    Test processing of location property data
    """

    def setUp(self) -> None:
        self.boolean_property = LocationProperty.objects.create(
            label='occupied', property_type='BOOL', required=True)
        self.date_property = LocationProperty.objects.create(
            label='build_year', property_type='DATE', required=True)
        self.email_property = LocationProperty.objects.create(
            label='mail_address', property_type='EMAIL', required=True)
        self.integer_property = LocationProperty.objects.create(
            label='number_of_floors', property_type='INT', required=True)
        self.string_property = LocationProperty.objects.create(
            label='building_color', property_type='STR', required=True)
        self.url_property = LocationProperty.objects.create(
            label='web_address', property_type='URL', required=True)
        self.choice_property = LocationProperty.objects.create(
            label='building_type', property_type='CHOICE', required=True)
        self.choice_option = PropertyOption.objects.create(
            location_property=self.choice_property, option='Office')

        # self.location = Location.objects.create(
        #     building_code='24000', name='Amstel 1',
        #     description='Stadhuis', active=True,
        #     street='Amstel', street_number='1',
        #     postal_code='1000 AA', city='Amsterdam',
        # )
        # self.location.locationdata_set.create(
        #     location_property = self.boolean_property, value = 'Ja'
        # )
        # self.location.locationdata_set.create(
        #     location_property = self.date_property, value = '01-12-2023'
        # )
        # self.location.locationdata_set.create(
        #     location_property = self.email_property, value = 'mail@example.org'
        # )
        # self.location.locationdata_set.create(
        #     location_property = self.integer_property, value = '11'
        # )
        # self.location.locationdata_set.create(
        #     location_property = self.string_property, value = 'Yellow'
        # )
        # self.location.locationdata_set.create(
        #     location_property = self.url_property, value = 'https://example.org'
        # )
        # self.location.locationdata_set.create(
        #     location_property = self.choice_property, property_option = self.choice_option
        # )

    def test_set_location_properties(self):
        """
        Verify if all the expected location fields and properties are filtered 
        correctly and present as attribute
        """
        # Field which are defined in the model
        expected_location_fields = {
            'building_code', 'name', 'short_name', 'description',
            'active', 'last_modified', 'street', 'street_number', 'street_number_letter',
            'street_number_extension', 'postal_code', 'city', 'construction_year',
            'floor_area', 'longitude', 'latitude', 'rd_x', 'rd_y', 'note'
        }
        # Location properties defined in the setup
        expected_location_properties = {
            'occupied', 'build_year', 'mail_address', 'number_of_floors', 'building_color',
            'web_address', 'building_type'
        }

        # Combined list
        combined_location_properties = expected_location_fields.union(expected_location_properties)

        # Location fields and properties filtered by _set_location_properties()
        processor = LocationDataProcessor()
        found_location_fields = set([
            field.name for field in processor.location_model_fields
        ])
        found_location_properties = set([
            instance.label for instance in processor.location_property_instances
        ])
        combined_found_properties = set(processor.location_properties_list)

        # Location field sets should be equal
        self.assertEqual(expected_location_fields, found_location_fields)
        # Location property sets should be equal
        self.assertEqual(expected_location_properties, found_location_properties)
        # Combined set should be equal
        self.assertEqual(combined_location_properties, combined_found_properties)

        # All expected fields should have an attribute
        for field in combined_location_properties:
            self.assertTrue(hasattr(processor, field), field)

    def test_init_with_data(self):
        """
        Test if an instancve of LocationDataProcessor is created
        and if the attributes have the correct value
        """
        location = LocationDataProcessor({
            'building_code': '24000',
            'name': 'Amstel 1',
            'description': 'Stadhuis',
            'active': True,
            'street': 'Amstel',
            'street_number': '1',
            'postal_code': '1000 AA',
            'city': 'Amsterdam',
            'occupied': 'Ja',
            'build_year': '01-12-2023',
            'mail_address': 'mail@example.org',
            'number_of_floors': '11',
            'building_color': 'Yellow',
            'web_address': 'https://example.org',
            'building_type': 'Office',
        })

        # Verifiy the instance and the attribute values
        self.assertIsInstance(location, LocationDataProcessor)
        self.assertEqual(location.building_code, '24000')
        self.assertEqual(location.name, 'Amstel 1')
        self.assertEqual(location.description, 'Stadhuis')
        self.assertEqual(location.active, True)
        self.assertEqual(location.street, 'Amstel')
        self.assertEqual(location.street_number, '1')
        self.assertEqual(location.postal_code, '1000 AA')
        self.assertEqual(location.city, 'Amsterdam')
        self.assertEqual(location.occupied, 'Ja')
        self.assertEqual(location.build_year, '01-12-2023')
        self.assertEqual(location.mail_address, 'mail@example.org')
        self.assertEqual(location.number_of_floors, '11')
        self.assertEqual(location.building_color, 'Yellow')
        self.assertEqual(location.web_address, 'https://example.org')
        self.assertEqual(location.building_type, 'Office')

    def test_location_save(self):
        """
        Test if a LocationDataProcessor object can be saved in the DB
        as a Location and related LocationData
        """
        # Check that no location exists in the database
        Location.objects.all().delete()
        self.assertEqual(Location.objects.all().count(), 0)
        # Save a location
        location = LocationDataProcessor({
            'building_code': '24000',
            'name': 'Amstel 1',
            'description': 'Stadhuis',
            'active': True,
            'street': 'Amstel',
            'street_number': '1',
            'postal_code': '1000 AA',
            'city': 'Amsterdam',
            'occupied': 'Ja',
            'build_year': '01-12-2023',
            'mail_address': 'mail@example.org',
            'number_of_floors': '11',
            'building_color': 'Yellow',
            'web_address': 'https://example.org',
            'building_type': 'Office',
        })
        location.save()

        # Check if the location has been added to the database
        # Only one location should exist in the database
        self.assertEqual(Location.objects.all().count(), 1)

        get_location = Location.objects.get(building_code='24000')

        # Check the attribute values for the Location() instance
        self.assertEqual(get_location.building_code, 24000)
        self.assertEqual(get_location.name, 'Amstel 1')
        self.assertEqual(get_location.description, 'Stadhuis')
        self.assertTrue(get_location.active)
        self.assertEqual(get_location.street, 'Amstel')
        self.assertEqual(get_location.street_number, 1)
        self.assertEqual(get_location.postal_code, '1000 AA')
        self.assertEqual(get_location.city, 'Amsterdam')
        # Check the LocationData() values
        location_data = get_location.locationdata_set.all()
        self.assertEqual(location_data[0].location_property, self.boolean_property)
        self.assertEqual(location_data[0].value, 'Ja')
        self.assertEqual(location_data[1].location_property, self.date_property)
        self.assertEqual(location_data[1].value, '01-12-2023')
        self.assertEqual(location_data[2].location_property, self.email_property)
        self.assertEqual(location_data[2].value, 'mail@example.org')
        self.assertEqual(location_data[3].location_property, self.integer_property)
        self.assertEqual(location_data[3].value, '11')
        self.assertEqual(location_data[4].location_property, self.string_property)
        self.assertEqual(location_data[4].value, 'Yellow')
        self.assertEqual(location_data[5].location_property, self.url_property)
        self.assertEqual(location_data[5].value, 'https://example.org')
        self.assertEqual(location_data[6].location_property, self.choice_property)
        self.assertEqual(location_data[6].property_option, self.choice_option)

    @mock.patch('locations.validators.LocationDataValidator.valid_choice')
    def test_location_save_atomic(self, mock):
        """
        Test that neither a Location or LocationData will be added to the DB
        if an error occurs during save()
        """
        location = LocationDataProcessor({
            'building_code': '24000',
            'name': 'Amstel 1',
            'description': 'Stadhuis',
            'active': True,
            'street': 'Amstel',
            'street_number': '1',
            'postal_code': '1000 AA',
            'city': 'Amsterdam',
            'occupied': 'Ja',
            'build_year': '01-12-2023',
            'mail_address': 'mail@example.org',
            'number_of_floors': '11',
            'building_color': 'Yellow',
            'web_address': 'https://example.org',
            'building_type': 'Kantoor',
        })
        mock.return_value = 'Office'
        # Mock the return value for validation of a boolean so no error is raised
        self.assertRaises(ObjectDoesNotExist, location.save)
        self.assertEqual(Location.objects.all().count(), 0)        

    def test_validation(self):
        location = LocationDataProcessor({
            'building_code': '24000',
            'name': 'Amstel 1',
            'description': 'Stadhuis',
            'active': True,
            'street': 'Amstel',
            'street_number': '1',
            'postal_code': '1000 AA',
            'city': 'Amsterdam',
            'build_year': '01-12-2023',
            'mail_address': 'mail@example.org',
            'number_of_floors': '11',
            'building_color': 'Yellow',
            'web_address': 'https://example.org',
            'building_type': 'Office',
        })
        self.assertRaises(ValidationError, location.validate)

        location = LocationDataProcessor({
            'building_code': '24000',
            'name': 'Amstel 1',
            'description': 'Stadhuis',
            'active': True,
            'street': 'Amstel',
            'street_number': '1',
            'postal_code': '1000 AA',
            'city': 'Amsterdam',
            'occupied': '',
            'build_year': '01-12-2023',
            'mail_address': 'mail@example.org',
            'number_of_floors': '11',
            'building_color': 'Yellow',
            'web_address': 'https://example.org',
            'building_type': 'Office',
        })
        self.assertRaises(ValidationError, location.validate)

    def test_location_get(self):
        location = LocationDataProcessor({
            'building_code': '24000',
            'name': 'Amstel 1',
            'description': 'Stadhuis',
            'active': True,
            'street': 'Amstel',
            'street_number': '1',
            'postal_code': '1000 AA',
            'city': 'Amsterdam',
            'occupied': 'Ja',
            'build_year': '01-12-2023',
            'mail_address': 'mail@example.org',
            'number_of_floors': '11',
            'building_color': 'Yellow',
            'web_address': 'https://example.org',
            'building_type': 'Office',
        })
        location.save()

        get_location = LocationDataProcessor.get(building_code='24000')

        # Verifiy the instance and the attribute values
        self.assertIsInstance(get_location, LocationDataProcessor)
        self.assertEqual(get_location.building_code, 24000) # TODO: string -> int, is dat erg?
        self.assertEqual(get_location.name, 'Amstel 1')
        self.assertEqual(get_location.description, 'Stadhuis')
        self.assertEqual(get_location.active, True)
        self.assertEqual(get_location.street, 'Amstel')
        self.assertEqual(get_location.street_number, 1)
        self.assertEqual(get_location.postal_code, '1000 AA')
        self.assertEqual(get_location.city, 'Amsterdam')
        self.assertEqual(get_location.occupied, 'Ja')
        self.assertEqual(get_location.build_year, '01-12-2023')
        self.assertEqual(get_location.mail_address, 'mail@example.org')
        self.assertEqual(get_location.number_of_floors, '11')
        self.assertEqual(get_location.building_color, 'Yellow')
        self.assertEqual(get_location.web_address, 'https://example.org')
        self.assertEqual(get_location.building_type, 'Office')

    def test_dict_method(self):...
