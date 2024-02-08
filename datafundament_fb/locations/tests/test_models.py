import unittest.mock as mock
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db.models.deletion import RestrictedError
from django.db.utils import IntegrityError
from django.db import transaction
from locations.models import compute_pandcode, validate_short_name, Location, LocationProperty, PropertyOption, LocationData, ExternalService, LocationExternalService
from locations import validators


class TestModelFunctions(TestCase):
    """
    Test custom model functions
    """

    def setUp(self) -> None:
        self.location1 = Location(pandcode='25000', name='Stopera')
        self.location2 = Location(pandcode='24000', name='GGD')
        self.location_property = LocationProperty(
            short_name='short_name', label="Short Name", property_type = 'STR')
        self.choice_property = LocationProperty.objects.create(
            label='Choice', property_type='CHOICE')

    def test_compute_pandcode(self):
        """
        Test auto compute of the building code in Location based on the current highest number
        """

        # Test when there is no Location object yet in the db
        self.assertEqual(Location.objects.all().count(), 0)
        self.assertEqual(compute_pandcode(), 1)

        # Test when there are existing location objects
        self.location1.save()
        self.location2.save()
        location_with_highest_pandcode = Location.objects.all().order_by('-pandcode').first()
        next_pandcode = location_with_highest_pandcode.pandcode + 1
        self.assertEqual(compute_pandcode(), next_pandcode)

    def test_short_name_validation(self):
        """
        Test validator for the short_name field
        """
        # Test the validator
        self.location_property.short_name = 'short_name'
        self.assertEqual(validate_short_name(self.location_property.short_name), self.location_property.short_name)
        self.location_property.short_name = 'shortname'
        self.assertEqual(validate_short_name(self.location_property.short_name), self.location_property.short_name)
        self.location_property.short_name = 'shortname1'
        self.assertEqual(validate_short_name(self.location_property.short_name), self.location_property.short_name)

        # Test for validation errors
        # Beginning with a number
        self.location_property.short_name = '1_name'
        self.assertRaises(ValidationError, self.location_property.full_clean)

        # To long
        self.location_property.short_name = 'to_long_name'
        self.assertRaises(ValidationError, self.location_property.full_clean)

        # Invalid characters
        self.location_property.short_name = 'short-name'
        self.assertRaises(ValidationError, self.location_property.full_clean)
        self.location_property.short_name = 'short name'
        self.assertRaises(ValidationError, self.location_property.full_clean)
        self.location_property.short_name = 'Shortname'
        self.assertRaises(ValidationError, self.location_property.full_clean)


class TestLocationDataValidation(TestCase):
    """
    Test for the validation of location property values 
    """

    def test_boolean_validation(self):
        # Test valid boolean value
        values = ['Ja', 'Nee']
        for value in values:
            self.assertEqual(validators.valid_boolean(value), value)

        # Test for invalid boolean called 'maybe'
        self.assertRaises(ValidationError, validators.valid_boolean, 'maybe')
        
    def test_date_validation(self):
        # Test valid date values
        values = ['31-12-2000', '1-1-2000', '29-02-2004']
        for value in values:
            self.assertEqual(validators.valid_date(value), value)

        # Test invalid date values
        values = ['12-31-2000', '29-02-2001', '31-12-20', '31-04-2000']
        for value in values:
            self.assertRaises(ValidationError, validators.valid_date, value)

    def test_email_validation(self):
        # Test valid email values
        values = [
            'test@example.nl',
            'test_test@example.com',
            'test+test@example.amsterdam'
        ]
        for value in values:
            self.assertEqual(validators.valid_email(value), value)

        # Test invalid email values
        values = [
            'test@example',
            'test@example.amsterdam.'
            'test@test@example.nl'
        ]
        for value in values:
            self.assertRaises(ValidationError, validators.valid_email, value)

    def test_int_validation(self):
        # Test valid integer values
        values = ['1', '0', '-100', '-1,1', '0,5', '16,3635']
        for value in values:
            self.assertEqual(validators.valid_integer(value), value)

        # Test invalid integer values
        values = ['0.5', '.5', ',5', '100.239,00']
        for value in values:
            self.assertRaises(ValidationError, validators.valid_integer, value)

    def test_memo_validation(self):
        # Test valid string value; this functions always returns the input, because the value it is already a string
        value = 'string'
        self.assertEqual(validators.valid_memo(value), value)

    def test_postal_code_validation(self):
        # Test valid postal codes
        values = ['1234AA', '1234 AA']
        for value in values:
            self.assertEqual(validators.valid_postal_code(value), value)

        # Test for invalid postal codes
        values = ['1234A', '123 AA', '1234aa', '0234 AA', '1234SS']
        for value in values:
            self.assertRaises(ValidationError, validators.valid_postal_code, value)

    def test_str_validation(self):
        # Test valid string value; this functions always returns the input, because the value it is already a string
        value = 'string'
        self.assertEqual(validators.valid_string(value), value)

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
            self.assertEqual(validators.valid_url(value), value)

        # Test invalid email values
        values = [
            'example.org'
            'http:/example.org',
            'http://www_example.org',
            'http:// example.org',
        ]
        for value in values:
            self.assertRaises(ValidationError, validators.valid_url, value)

    def test_choice_validation(self):
        choice_property = LocationProperty.objects.create(
            short_name='choice', label='Choice', property_type='CHOICE')
        PropertyOption.objects.create(
            location_property=choice_property, option='Yellow')
        PropertyOption.objects.create(
            location_property=choice_property, option='Orange')

        # Test valid choice value input
        value = 'Yellow'
        validator = validators.ChoiceValidator(choice_property)
        self.assertEqual(validator(value), value)

        # Test invalid choice value input; Magenta does not exist, yellow only exists with capital Y
        with self.assertRaises(ValidationError):
            validator('Magenta')
        with self.assertRaises(ValidationError):
            validator('yellow')

    def test_multiple_choice_validation(self):
        choice_property = LocationProperty.objects.create(
            short_name='choice', label='Choice', property_type='CHOICE', multiple=True)
        PropertyOption.objects.create(
            location_property=choice_property, option='Yellow')
        PropertyOption.objects.create(
            location_property=choice_property, option='Orange')

        # Test valid choice value input
        value = ['Yellow', 'Orange']
        validator = validators.ChoiceValidator(choice_property)
        self.assertEqual(validator(value), value)

        # Test invalid choice value input; Magenta does not exist, yellow only exists with capital Y
        with self.assertRaises(ValidationError):
            validator(['Yellow', 'Magenta'])
        with self.assertRaises(ValidationError):
            validator(['yellow', 'orange'])


class TestGetLocationDataValidate(TestCase):
    """
    Test if the correct validation method is selected when running the validate() function in get_locationdata_validator
    """

    def setUp(self) -> None:
        self.location1 = Location.objects.create(pandcode='25000', name='Stopera')
        self.location2 = Location.objects.create(pandcode='24000', name='GGD')
        self.boolean_property = LocationProperty.objects.create(
            short_name='bool', label='Boolean', property_type='BOOL')
        self.date_property = LocationProperty.objects.create(
            short_name='date', label='Date', property_type='DATE')
        self.email_property = LocationProperty.objects.create(
            short_name='mail', label='Email', property_type='EMAIL')
        self.integer_property = LocationProperty.objects.create(
            short_name='int', label='Integer', property_type='INT')
        self.memo_property = LocationProperty.objects.create(
            short_name='memo', label='Memo', property_type='MEMO')
        self.postal_code_property = LocationProperty.objects.create(
            short_name='post', label='Postal code', property_type='POST')
        self.string_property = LocationProperty.objects.create(
            short_name='str', label='String', property_type='STR')
        self.url_property = LocationProperty.objects.create(
            short_name='url', label='Url', property_type='URL')
        self.choice_property = LocationProperty.objects.create(
            short_name='choice', label='Choice', property_type='CHOICE')
        self.choice_option_1 = PropertyOption.objects.create(
            location_property=self.choice_property, option='Yellow')
        self.choice_option_2 = PropertyOption.objects.create(
            location_property=self.choice_property, option='Orange')
        self.location_data = LocationData(location=self.location1)

    @mock.patch('locations.validators.valid_boolean')
    def test_clean_boolean(self, mock):
        # Test if valid_boolean() is called
        value = 'Ja'
        validators.get_locationdata_validator(
            location_property=self.boolean_property, value=value)
        self.assertTrue(mock.called)

    @mock.patch('locations.validators.valid_date')
    def test_clean_date(self, mock):
        # Test if valid_date() is called
        value = '31-12-2000'
        validators.get_locationdata_validator(
            location_property=self.date_property, value=value)
        self.assertTrue(mock.called)

    @mock.patch('locations.validators.valid_integer')
    def test_clean_integer(self, mock):
        # Test if valid_integer is called
        value = '1'
        validators.get_locationdata_validator(
            location_property=self.integer_property, value=value)
        self.assertTrue(mock.called)

    @mock.patch('locations.validators.valid_memo')
    def test_clean_memo(self, mock):
        # Test if valid_integer is called
        value = 'string'
        validators.get_locationdata_validator(
            location_property=self.memo_property, value=value)
        self.assertTrue(mock.called)

    @mock.patch('locations.validators.valid_postal_code')
    def test_clean_postal_code(self, mock):
        # Test if valid string is called
        value = '1234 AA'
        validators.get_locationdata_validator(
            location_property=self.postal_code_property, value=value)
        self.assertTrue(mock.called)

    @mock.patch('locations.validators.valid_string')
    def test_clean_string(self, mock):
        # Test if valid string is called
        value = 'string'
        validators.get_locationdata_validator(
            location_property=self.string_property, value=value)
        self.assertTrue(mock.called)

    @mock.patch('locations.validators.valid_url')
    def test_clean_url(self, mock):
        # Test if valid_url is called
        value = 'http://example.org'
        validators.get_locationdata_validator(
            location_property=self.url_property, value=value)
        self.assertTrue(mock.called)

    @mock.patch('locations.validators.ChoiceValidator')
    def test_validate_choice(self, mock):
        # Test if valid_choice is called
        value = 'Yellow'
        validators.get_locationdata_validator(
            location_property=self.choice_property, value=value)
        self.assertTrue(mock.called)


class TestLocationDataModel(TestCase):
    """
    Test added code to the LocationData model
    """

    def setUp(self) -> None:
        self.location = Location.objects.create(pandcode='25000', name='Stopera')
        self.location2 = Location.objects.create(pandcode='25001', name='GGD')
        self.string_property = LocationProperty.objects.create(
            short_name='str', label='String', property_type='STR', unique=True)
        self.choice_property = LocationProperty.objects.create(
            label='Choice', property_type='CHOICE')
        self.choice_option = PropertyOption.objects.create(
            location_property=self.choice_property, option='Yellow')
        self.location_data = LocationData(location=self.location)
    
    def test_required_field(self):
        # Test when location_property is required and no value or option is passed
        # Make the location property required
        self.choice_property.required = True

        # Set LocationData without value
        self.location_data = LocationData(
            location=self.location,
            location_property=self.choice_property,
        )
        self.assertRaises(ValidationError, self.location_data.clean)

    def test_for_empty_value_constraint(self):
        # Test when either field is filled, not both
        self.location_data.location_property = self.choice_property
        self.location_data.property_option = self.choice_option
        self.assertEqual(self.location_data.clean(), None)

        self.location_data.property_option = None
        self.location_data.value = 'Yellow'
        self.assertEqual(self.location_data.clean(), None)

        # Integrity error is raised when both fields are filled
        self.location_data.property_option = self.choice_option
        self.location_data.value = 'Yellow'
        # Prevent the error from breaking the transaction, atomic is needed
        with transaction.atomic():
            self.assertRaises(IntegrityError, self.location_data.save)

    def test_for_unique_constraint(self):
        # Test when unique is enabled
        # Save a value to the database
        self.location_data.location_property = self.string_property
        self.location_data.value = 'Yellow'
        self.location_data.save()

        # Add location_data to second location with an existing value
        location_data = LocationData(
            location=self.location2,
            location_property = self.string_property,
            value = 'Yellow'
        )
        # Raise a validation error
        with self.assertRaises(ValidationError) as validation_error:
            location_data.clean()

        # Test the validation error
        self.assertEqual(validation_error.exception.code, 'unique')
        self.assertEqual(
            validation_error.exception.message,
            f'Waarde %(value)s bestaat al voor eigenschap %(property)s.',
        )

    def test_for_single_constraint(self):
        # Test that a property can only exist once for a location; except when multiple is enabled for a property
        self.location_data.location_property = self.string_property
        self.location_data.value = 'Yellow'
        self.location_data.save()

        # Create a new LocationData
        location_data = LocationData(
            location=self.location,
            location_property = self.string_property,
            value = 'Orange'
        )

        # Raise a validation error with full_clean()
        with self.assertRaises(ValidationError) as validation_error:
            location_data.clean()

        # Test the validation error
        self.assertEqual(validation_error.exception.code, 'unique')
        self.assertEqual(
            validation_error.exception.message,
            f'De locatie eigenschap %(property)s bestaat al voor locatie %(location)s.',
        )

        # Test when multiple is enabled for a property
        self.string_property.multiple = True
        self.string_property.save()
        
        # Create a new LocationData
        location_data = LocationData.objects.create(
            location=self.location,
            location_property = self.string_property,
            value = 'Orange'
        )

        # Verify that the same property is added to the location twice
        location_data = Location.objects.get(pandcode=self.location.pandcode).locationdata_set.all()
        self.assertEqual(len(location_data), 2)
        self.assertEqual(location_data[0].value, 'Yellow')
        self.assertEqual(location_data[1].value, 'Orange')
        for item in Location.objects.get(pandcode=self.location.pandcode).locationdata_set.all():
            self.assertEqual(item.location, self.location)
            self.assertEqual(item.location_property, self.string_property)


class TestReferencedModelOnDelete(TestCase):
    """
    Explicity test the on_delete attribute for models with foreign keys
    """

    def setUp(self) -> None:
        self.location = Location.objects.create(pandcode=25000, name='Stadhuis')
        self.location_property = LocationProperty.objects.create(
            short_name='property', label='Location property', property_type='CHOICE')
        self.property_option = PropertyOption.objects.create(
            location_property=self.location_property, option='Optiewaarde 1')
        self.location_data = LocationData.objects.create(
            location=self.location, location_property=self.location_property, property_option=self.property_option)
        self.external_service = ExternalService.objects.create(
            name='Externe service', short_name='ext_srv')
        self.location_external_service = LocationExternalService.objects.create(
            location=self.location, external_service=self.external_service, external_location_code='code'
        )

    def test_location_cascading(self):
        """
        When deleting a location, referenced intances in LocationData
        and LocationExternalService should also be removed from the database
        """

        # Delete the Location
        self.location.delete()
        
        # Verify cascading of the referenced models
        # There should be 0 instances left of the following models
        self.assertEqual(len(Location.objects.all()), 0)
        self.assertEqual(len(LocationData.objects.all()), 0)
        self.assertEqual(len(LocationExternalService.objects.all()), 0)

        # There should be 1 instance left of the following models
        self.assertEqual(len(LocationProperty.objects.all()), 1)
        self.assertEqual(len(PropertyOption.objects.all()), 1)
        self.assertEqual(len(ExternalService.objects.all()), 1)

    def test_location_property_cascading(self):
        """
        When deleting a location property, referenced instances in LocationData and
        PropertyOptions should als be removed  
        """
        # Delete the LocationProperty
        self.location_property.delete()

        # Verify cascading of the referenced models
        # There should be 0 instances left of the following models
        self.assertEqual(len(LocationProperty.objects.all()), 0)
        self.assertEqual(len(LocationData.objects.all()), 0)
        self.assertEqual(len(PropertyOption.objects.all()), 0)

        # There should be 1 instance left of the following models
        self.assertEqual(len(Location.objects.all()), 1)
        self.assertEqual(len(ExternalService.objects.all()), 1)
        self.assertEqual(len(LocationExternalService.objects.all()), 1)

    def test_property_option_restriction(self):
        """
        When deleting a property option, restriction should be enforced
        if there is a referenced LocationData instance
        """

        # Deleting a referenced PropertyOption should result in a restriction exception 
        self.assertRaises(RestrictedError, self.property_option.delete)

        # There should be 1 instances left of the following models
        self.assertEqual(len(PropertyOption.objects.all()), 1)
        self.assertEqual(len(LocationProperty.objects.all()), 1)
        self.assertEqual(len(LocationData.objects.all()), 1)
        self.assertEqual(len(Location.objects.all()), 1)
        self.assertEqual(len(ExternalService.objects.all()), 1)
        self.assertEqual(len(LocationExternalService.objects.all()), 1)

        # Delete the referenced LocationData instance
        self.location_data.delete()
        # Verify that there are no LocationData instances
        self.assertEqual(len(LocationData.objects.all()), 0)

        # Deletion should now be possible
        self.property_option.delete()
        # Verify that there is no PropertyOption anymore
        self.assertEqual(len(PropertyOption.objects.all()), 0)

    def test_external_service_cascading(self):
        """
        When an ExternalService instance is deleted, the referenced LocationExternalService instance
        should als be removed
        """

        # Delete the ExternalService
        self.external_service.delete()

        # Verify that the ExternalService and referenced LocationExternalService instance has been deleted
        self.assertEqual(len(ExternalService.objects.all()), 0)
        self.assertEqual(len(LocationExternalService.objects.all()), 0)
