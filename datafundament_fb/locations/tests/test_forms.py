from unittest import skip
from django import forms
from django.core.files.base import ContentFile
from django.test import TestCase
from django.urls import reverse
from locations.forms import LocationImportForm
from locations.models import Location, LocationProperty, PropertyOption, LocationData


class TestLocationImportForm(TestCase):
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
        self.choice_option_ = PropertyOption.objects.create(
            location_property=self.choice_property, option='Orange')

    def test_import_csv_get(self):
        """Get the form"""
        response = self.client.get(reverse('location-import'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Locaties importeren', str(response.content))


    def test_import_csv_post(self):
        """Post the form"""
        csv_content  = [
            'pandcode,naam,bool,date,mail,int,memo,post,str,url,choice',
            '25001,GGD,Amstel 1,Ja,31-12-2023,mail@example.org,99,Memo tekst,1234AB,Tekst,https://exampleorg,Yellow'
        ]
        csv_file = ContentFile('\n'.join(csv_content).encode())
        data = {'csv_file': csv_file}
        response = self.client.post(reverse('location-import'), data)
        breakpoint()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], reverse('location-import'))  

    # TEST MESSSAGE FOR USED COLUMNS
    # TEST MESSAGE FOR FAILURE...
    # TEST FOR SUCCES MESSAGE
    # CHECK FOR INVALID FILE