from django import forms
from django.test import TestCase
from locations.forms import LocationDataForm
from locations.models import Location, LocationProperty, PropertyOption


class TestLocationDataForm(TestCase):
    def setUp(self) -> None:
        self.location = Location.objects.create(pandcode='25000', name='Stopera')
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
        self.location_data_form = LocationDataForm()

    def test_location_property_form_fields(self):
        """
        Test if a form field is set for each location property type, ie:, BOOL, INT, etc 
        """
        
        # Check for all location property fields

        # Boolean field
        field = self.location_data_form.fields[self.boolean_property.short_name] 
        self.assertIsInstance(field, forms.ChoiceField)
        self.assertEqual(field.label, self.boolean_property.label)

        # Date field
        field = self.location_data_form.fields[self.date_property.short_name] 
        self.assertIsInstance(field, forms.CharField)
        self.assertEqual(field.label, self.date_property.label)

        # Email field
        field = self.location_data_form.fields[self.email_property.short_name] 
        self.assertIsInstance(field, forms.CharField)
        self.assertEqual(field.label, self.email_property.label)

        # Integer field
        field = self.location_data_form.fields[self.integer_property.short_name] 
        self.assertIsInstance(field, forms.CharField)
        self.assertEqual(field.label, self.integer_property.label)

        # Memo field
        field = self.location_data_form.fields[self.memo_property.short_name] 
        self.assertIsInstance(field, forms.CharField)
        self.assertEqual(field.label, self.memo_property.label)

        # Postal code field
        field = self.location_data_form.fields[self.postal_code_property.short_name] 
        self.assertIsInstance(field, forms.CharField)
        self.assertEqual(field.label, self.postal_code_property.label)

        # String field
        field = self.location_data_form.fields[self.string_property.short_name] 
        self.assertIsInstance(field, forms.CharField)
        self.assertEqual(field.label, self.string_property.label)

        # Url field
        field = self.location_data_form.fields[self.url_property.short_name] 
        self.assertIsInstance(field, forms.CharField)
        self.assertEqual(field.label, self.url_property.label)

        # Choice field
        field = self.location_data_form.fields[self.choice_property.short_name] 
        self.assertIsInstance(field, forms.ChoiceField)
        self.assertEqual(field.label, self.choice_property.label)

        # Test for error when a property type that is not defined is matched
        undefined_property = LocationProperty.objects.create(short_name='undefined', label='Undefined property', property_type='undefined')
        field = self.location_data_form.fields[self.boolean_property.short_name] 
        with self.assertRaises(ValueError) as value_error:
            LocationDataForm()
        
        # Verify the error message
        self.assertIn(
            f"No form field defined for '{undefined_property.property_type}'",
            value_error.exception.__str__()
        )
