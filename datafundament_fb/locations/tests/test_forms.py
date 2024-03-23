from django import forms
from django.contrib.auth.models import User, AnonymousUser
from django.test import TestCase
from locations.forms import LocationDataForm, LocationListForm
from locations.models import Location, LocationProperty, PropertyOption, ExternalService
from locations.processors import LocationProcessor

class TestLocationDataForm(TestCase):
    def setUp(self) -> None:
        self.location = Location.objects.create(pandcode='25000', name='Stopera')
        self.boolean_property = LocationProperty.objects.create(
            short_name='bool', label='Boolean', property_type='BOOL')
        self.date_property = LocationProperty.objects.create(
            short_name='date', label='Date', property_type='DATE')
        self.email_property = LocationProperty.objects.create(
            short_name='mail', label='Email', property_type='EMAIL')
        self.geolocation_property = LocationProperty.objects.create(
            short_name='geo', label='Geolocation', property_type='GEO')
        self.number_property = LocationProperty.objects.create(
            short_name='num', label='number', property_type='NUM')
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
        self.multichoice_property = LocationProperty.objects.create(
            short_name='multichoic', label='Multiple choice', property_type='CHOICE', multiple=True)
        self.multi_choice_option_1 = PropertyOption.objects.create(
            location_property=self.multichoice_property, option='Car')
        self.choice_option_2 = PropertyOption.objects.create(
            location_property=self.multichoice_property, option='Bus')
        self.external_service = ExternalService.objects.create(
            name='Externe service', short_name='extservice')
        self.user = User.objects.create(username='testuser', is_superuser=False, is_staff=True)
        self.location_data_form = LocationDataForm(user=self.user)

    def test_location_property_form_fields(self):
        """
        Test if a form field is set for each location property type, ie:, BOOL, NUM, etc 
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

        # Geolocation field
        field = self.location_data_form.fields[self.geolocation_property.short_name] 
        self.assertIsInstance(field, forms.CharField)
        self.assertEqual(field.label, self.geolocation_property.label)

        # number field
        field = self.location_data_form.fields[self.number_property.short_name] 
        self.assertIsInstance(field, forms.CharField)
        self.assertEqual(field.label, self.number_property.label)

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

        # Multiple choice field
        field = self.location_data_form.fields[self.multichoice_property.short_name] 
        self.assertIsInstance(field, forms.MultipleChoiceField)
        self.assertEqual(field.label, self.multichoice_property.label)

        # External service field
        field = self.location_data_form.fields[self.external_service.short_name] 
        self.assertIsInstance(field, forms.CharField)
        self.assertEqual(field.label, self.external_service.name)

        # Test for error when a property type that is not defined is matched
        undefined_property = LocationProperty.objects.create(short_name='undefined', label='Undefined property', property_type='onbekend')
        field = self.location_data_form.fields[self.boolean_property.short_name] 
        with self.assertRaises(ValueError) as value_error:
            LocationDataForm(user=self.user)
        
        # Verify the error message
        self.assertIn(
            f"Er bestaat geen formulierveld voor '{undefined_property.property_type}'.",
            value_error.exception.__str__()
        )

class TestLocationListForm(TestCase):
    def setUp(self) -> None:
        self.public_property = LocationProperty.objects.create(
            short_name='public', label='Public property', property_type='STR', public=True)
        self.private_property = LocationProperty.objects.create(
            short_name='private', label='Private property', property_type='STR', public=False)
        self.choice_property = LocationProperty.objects.create(
            short_name='choice', label='choice property', property_type='CHOICE', public=False)
        self.property_option = PropertyOption.objects.create(
            location_property=self.choice_property, option='Keuze optie')
        self.external_service = ExternalService.objects.create(
            name='External service', short_name='external', public=True)
        Location.objects.create(
            pandcode=24001, name='Stadhuis', is_archived=False)
        Location.objects.create(
            pandcode=24002, name='Stopera', is_archived=False)
        Location.objects.create(
            pandcode=24003, name='Ambtswoning', is_archived=True )
        self.user = User.objects.create(username='testuser', is_superuser=False, is_staff=True)
        LocationProcessor(user=self.user, data={
            'pandcode': '24001',
            'naam': 'Stadhuis',
            'public': 'Publieke info',
            'private': 'Private info',
            'choice': 'Keuze optie',
            'external': 'Externe code 24001',
        }).save()
        LocationProcessor(user=self.user, data={
            'pandcode': '24002',
            'naam': 'Stopera',
            'public': 'Publieke info',
            'private': 'Private info',
            'choice': 'Keuze optie',
            'external': 'Externe code 24002',
        }).save()
        LocationProcessor(user=self.user, data={
            'pandcode': '24003',
            'naam': 'Ambtswoning',
            'public': 'Publieke info',
            'private': 'Private info',
            'choice': 'Keuze optie',
            'external': 'Externe code 24003',
        }).save()

    def test_search_form_fields_authenticated(self):
        # Render the form as an authenticated user
        location_list_form = LocationListForm(user=self.user)

        # Verify the form fields
        # Property field
        field = location_list_form.fields['property'] 
        self.assertIsInstance(field, forms.ChoiceField)
        # Verify the choices in the properties list
        expected_choice_list = [
            ('','Alle tekstvelden'),
            ('naam','Naam'),
            ('pandcode','Pandcode'),
            (self.public_property.short_name, self.public_property.label),
            (self.private_property.short_name, self.private_property.label),
            (self.choice_property.short_name, self.choice_property.label),
            (self.external_service.short_name, self.external_service.name),
        ]
        self.assertEqual(set(field._choices), set(expected_choice_list))

        # Search field
        field = location_list_form.fields['search'] 
        self.assertIsInstance(field, forms.CharField)

        # Select field for the choice property
        field = location_list_form.fields[self.choice_property.short_name]
        self.assertIsInstance(field, forms.ChoiceField)
        # Verify if the choice is in the list of choices
        self.assertIn(self.property_option.option, field._choices[0])

    def test_search_form_field_anonymous(self):
        # Render the form as an anonymous user
        user = AnonymousUser()
        location_list_form = LocationListForm(user=user)

        # Verify the form fields
        # Property field
        field = location_list_form.fields['property'] 
        self.assertIsInstance(field, forms.ChoiceField)
        # Verify the choices in the properties list
        expected_choice_list = [
            ('','Alle tekstvelden'),
            ('naam','Naam'),
            ('pandcode','Pandcode'),
            (self.public_property.short_name, self.public_property.label),
            (self.external_service.short_name, self.external_service.name),
        ]
        self.assertEqual(set(field._choices), set(expected_choice_list))

        # Search field
        field = location_list_form.fields['search'] 
        self.assertIsInstance(field, forms.CharField)

        # The choice property should not have a select field
        field = location_list_form.fields.get(self.choice_property.short_name, None)
        self.assertIsNone(field)
