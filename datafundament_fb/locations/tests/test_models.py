from django.test import TestCase
from django.core.exceptions import ValidationError
from locations.models import compute_building_code, validate_postal_code, Location, LocationProperty, PropertyOption, LocationData
from locations.validators import LocationDataValidator

class TestModelFunctions(TestCase):
    """
    Test custom model functions
    """

    def setUp(self) -> None:
        self.location1 = Location(building_code='25000', name='Stopera', description='Stadhuis',
                                  street='Amstel1', street_number=1, postal_code='1000 AA',
                                  city='Amsterdam')
        self.location2 = Location(building_code='24000', name='GGD', description='Gemeentelijke Gezondheidsdienst',
                                  street='Nieuw Achtergracht', street_number=100, postal_code='1018 BB',
                                  city='Amsterdam')

    def test_compute_building_code(self):
        """
        Test auto compute of the building code in Location based on the current highest number
        """

        # Test when there is no Location object yet in the db
        self.assertEqual(Location.objects.all().count(), 0)
        self.assertEqual(compute_building_code(), 1)

        # Test when there are existing location objects
        self.location1.save()
        self.location2.save()
        location_with_highest_building_code = Location.objects.all().order_by('-building_code').first()
        next_building_code = location_with_highest_building_code.building_code + 1
        self.assertEqual(compute_building_code(), next_building_code)

    def test_postal_code_validation(self):
        """
        Test  postal code validation
        """

        # Test the validator
        self.location1.postal_code = '1234 AA'
        self.assertEqual(validate_postal_code(self.location1.postal_code), self.location1.postal_code)

        # Test for validation errors
        # No space between the numbers and letters
        self.location1.postal_code = '1234AA'
        self.assertRaises(ValidationError, self.location1.full_clean)

        # Only one letter
        self.location1.postal_code = '1234 A'
        self.assertRaises(ValidationError, self.location1.full_clean)

        # Only 3 numbers
        self.location1.postal_code = '123 AA'
        self.assertRaises(ValidationError, self.location1.full_clean)

        # Letters in lower case
        self.location1.postal_code = '1234 aa'
        self.assertRaises(ValidationError, self.location1.full_clean)

        # Leading with a zero
        self.location1.postal_code = '0234 AA'
        self.assertRaises(ValidationError, self.location1.full_clean)

        # Prohibited combination of letters (SA, SD, SS)
        self.location1.postal_code = '1234 SS'
        self.assertRaises(ValidationError, self.location1.full_clean)


class TestLocationDataValidation(TestCase):
    """
    Test for the validation of location property values 
    """

    def setUp(self) -> None:
        self.location1 = Location.objects.create(building_code='25000', name='Stopera', description='Stadhuis',
                                  street='Amstel1', street_number=1, postal_code='1000 AA',
                                  city='Amsterdam')
        self.location2 = Location.objects.create(building_code='24000', name='GGD', description='Gemeentelijke Gezondheidsdienst',
                                  street='Nieuw Achtergracht', street_number=100, postal_code='1018 BB',
                                  city='Amsterdam')
        self.boolean_property = LocationProperty.objects.create(
            label='Boolean', property_type='BOOL')
        self.date_property = LocationProperty.objects.create(
            label='Date', property_type='DATE')
        self.email_property = LocationProperty.objects.create(
            label='Email', property_type='EMAIL')
        self.integer_property = LocationProperty.objects.create(
            label='Integer', property_type='INT')
        self.string_property = LocationProperty.objects.create(
            label='String', property_type='STR')
        self.url_property = LocationProperty.objects.create(
            label='Url', property_type='URL')
        self.choice_property = LocationProperty.objects.create(
            label='Choice', property_type='CHOICE')
        self.choice_option_1 = PropertyOption.objects.create(
            location_property=self.choice_property, option='Yellow')
        self.choice_option_2 = PropertyOption.objects.create(
            location_property=self.choice_property, option='Orange')
        self.location_data = LocationData(location=self.location1)

    def test_boolean_validation(self):
        # Test valid boolean value
        values = ['Ja', 'Nee']
        for value in values:
            self.assertEqual(LocationDataValidator.validate(
                self.boolean_property, value), value)

        # Test for invalid boolean called 'maybe'
        with self.assertRaises(ValidationError):
            value = 'maybe'
            LocationDataValidator.validate(self.boolean_property, value)
        
    def test_date_validation(self):
        # Test valid date values
        values = ['31-12-2000', '1-1-2000', '29-02-2004']
        for value in values:
            self.assertEqual(LocationDataValidator.validate(
                self.date_property, value), value)

        # Test invalid date values
        values = ['12-31-2000', '29-02-2001', '31-12-20', '31-04-2000']
        for value in values:
            with self.assertRaises(ValidationError):
                LocationDataValidator.validate(self.date_property, value)

    def test_email_validation(self):
        # Test valid email values
        values = [
            'test@example.nl',
            'test_test@example.com',
            'test+test@example.amsterdam'
        ]
        for value in values:
            self.assertEqual(LocationDataValidator.validate(
                self.email_property, value), value)

        # Test invalid email values
        values = [
            'test@example',
            'test@example.amsterdam.'
            'test@test@example.nl'
        ]
        for value in values:
            with self.assertRaises(ValidationError):
                LocationDataValidator.validate(self.email_property, value)

    def test_int_validation(self):
        # Test valid integer values
        values = ['1', '0', '-100', '-1,1', '0,5', '16,3635']
        for value in values:
            self.assertEqual(LocationDataValidator.validate(
                self.integer_property, value), value)

        # Test invalid integer values
        values = ['0.5', '.5', ',5', '100.239,00']
        for value in values:
            with self.assertRaises(ValidationError):
                LocationDataValidator.validate(self.integer_property, value)

    def test_str_validation(self):
        # Test valid string value; this functions always returns the input, because it is a string
        value = 'string'
        self.assertEqual(LocationDataValidator.validate(
            self.string_property, value), value)

    def test_url_validation(self):
        # Test valid URL values
        values = [
            'http://example.org',
            'http://www.example.org',
            'http://www-example.org',
            'https://example.org:8080',
            'https://example.org/path/to/dir',
            'https://example.org/path/to/dir/parameters?values',
        ]
        for value in values:
            self.assertEqual(LocationDataValidator.validate(
                self.url_property, value), value)

        # Test invalid email values
        values = [
            'example.org'
            'http:/example.org',
            'http://www_example.org',
            'http:// example.org',
        ]
        for value in values:
            with self.assertRaises(ValidationError):
                LocationDataValidator.validate(self.url_property, value)

    def test_choice_validation(self):
        # Test valid choice value input
        value = 'Yellow'
        self.assertEqual(LocationDataValidator.validate(
            self.choice_property, value), value)

        # Test invalid choice value input
        with self.assertRaises(ValidationError):
            value = 'Magenta'
            LocationDataValidator.validate(self.choice_property, value)
        with self.assertRaises(ValidationError):
            value = 'yellow'
            LocationDataValidator.validate(self.choice_property, value)


class TestLocationDataClean(TestCase):
    """
    Test the clean method LocationData 
    """

    def setUp(self) -> None:
        self.location1 = Location.objects.create(building_code='25000', name='Stopera', description='Stadhuis',
                                                 street='Amstel1', street_number=1, postal_code='1000 AA',
                                                 city='Amsterdam')
        self.location2 = Location.objects.create(building_code='24000', name='GGD', description='Gemeentelijke Gezondheidsdienst',
                                                 street='Nieuw Achtergracht', street_number=100, postal_code='1018 BB',
                                                 city='Amsterdam')
        self.boolean_property = LocationProperty.objects.create(
            label='Boolean', property_type='BOOL')
        self.date_property = LocationProperty.objects.create(
            label='Date', property_type='DATE')
        self.email_property = LocationProperty.objects.create(
            label='Email', property_type='EMAIL')
        self.integer_property = LocationProperty.objects.create(
            label='Integer', property_type='INT')
        self.string_property = LocationProperty.objects.create(
            label='String', property_type='STR')
        self.url_property = LocationProperty.objects.create(
            label='Url', property_type='URL')
        self.choice_property = LocationProperty.objects.create(
            label='Choice', property_type='CHOICE')
        self.choice_option_1 = PropertyOption.objects.create(
            location_property=self.choice_property, option='Yellow')
        self.choice_option_2 = PropertyOption.objects.create(
            location_property=self.choice_property, option='Orange')
        self.location_data = LocationData(location=self.location1)

    def test_clean_boolean(self):
        # Test valid boolean
        self.location_data.location_property = self.boolean_property
        self.location_data.value = 'Ja'
        self.assertEqual(self.location_data.clean(), None)

        # Test invalid boolean
        self.location_data.value = 'Maybe'
        self.assertRaises(ValidationError, self.location_data.clean)
          
    def test_clean_date(self):
        # Test valid date
        self.location_data.location_property = self.date_property
        self.location_data.value = '31-12-2000'
        self.assertEqual(self.location_data.clean(), None)

        # Test invalid date
        self.location_data.value = '12-31-2000'
        self.assertRaises(ValidationError, self.location_data.clean)

    def test_clean_integer(self):
        # Test valid integer
        self.location_data.location_property = self.integer_property
        self.location_data.value = '1'
        self.assertEqual(self.location_data.clean(), None)

        # Test invalid integer
        self.location_data.value = '1.1'
        self.assertRaises(ValidationError, self.location_data.clean)

    def test_clean_string(self):
        # Test valid string
        self.location_data.location_property = self.string_property
        self.location_data.value = 'string'
        self.assertEqual(self.location_data.clean(), None)

    def test_clean_string(self):
        # Test valid Url
        self.location_data.location_property = self.url_property
        self.location_data.value = 'http://example.org'
        self.assertEqual(self.location_data.clean(), None)

    def test_clean_choice(self):
        # Test valid choice
        self.location_data.location_property = self.choice_property
        self.location_data.property_option = self.choice_option_1
        self.location_data.value = ''
        # ValidationError is expected because the value in LocationData should be empty
        self.assertRaises(ValidationError, self.location_data.clean)