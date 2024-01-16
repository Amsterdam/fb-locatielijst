from django.contrib.messages import get_messages
from django.core.files.base import ContentFile
from django.test import TestCase
from django.urls import reverse
from locations.models import Location
from locations.models import Location, LocationProperty, PropertyOption


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
        self.csv_content  = [
            'pandcode,naam,bool,date,mail,int,memo,post,str,url,choice',
            '25001,Amstel 1,Ja,31-12-2023,mail@example.org,99,Memo tekst,1234AB,Tekst,https://example.org,Orange'
        ]

    def test_import_csv_get(self):
        """Get the form"""
        response = self.client.get(reverse('location-import'))

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'locations/location-import.html')
        self.assertIn('Locaties importeren', str(response.content))

    def test_import_csv_post(self):
        """Post the form"""
        csv_file = ContentFile('\n'.join(self.csv_content).encode(), name='import-file.csv')
        data = {'csv_file': csv_file}
        url = reverse('location-import')
        response = self.client.post(url, data)

        # Verify response
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], reverse('location-import'))  

        # Verify response messages
        messages = [msg for msg in get_messages(response.wsgi_request)]
        self.assertEqual(messages[0].tags, 'info')      
        self.assertEqual(messages[1].tags, 'success')      

        # Message with used columns
        message = messages[0].message
        message = message.replace('\'','')
        index_left = message.find('[')
        index_right = message.find(']')
        used_columns = message[index_left +1: index_right].split(', ')
        headers = self.csv_content[0].split(',')
        self.assertEqual(set(used_columns), set(headers))

        # Success message
        self.assertEqual(messages[1].message, f"Locatie Amstel 1 is geïmporteerd/ge-update")

        # Verify that the location instance
        location = Location.objects.get(pandcode=25001)
        self.assertEqual(location.name, 'Amstel 1')

    def test_import_csv_post_invalid_file(self):
        """Post the form with an invalid file extension"""
        xslx_file = ContentFile('\n'.join(self.csv_content).encode(), name='import-file.xlsx')
        data = {'csv_file': xslx_file}
        url = reverse('location-import')
        response = self.client.post(url, data)

        # Verify response
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], reverse('location-import'))  

        # Verify response message
        messages = [msg for msg in get_messages(response.wsgi_request)]
        self.assertEqual(messages[0].tags, 'error')
        self.assertEqual(messages[0].message, "import-file.xlsx is geen gelding CSV bestand")

    def test_import_csv_post_invalid_value(self):
        """Post the form with an invalid form value"""
        # CSV data
        csv_content  = [
            'pandcode,naam,bool,date,mail,int,memo,post,str,url,choice',
            '25001,Amstel 1,Misschien,31-12-2023,mail@example.org,99,Memo tekst,1234AB,Tekst,https://example.org,Yellow'
        ]
        csv_file = ContentFile('\n'.join(csv_content).encode(), name='import-file.csv')
        data = {'csv_file': csv_file}
        url = reverse('location-import')
        response = self.client.post(url, data)

        # Verify response
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], reverse('location-import'))  

        # Verify response message
        messages = [msg for msg in get_messages(response.wsgi_request)]
        self.assertEqual(messages[1].tags, 'error')
        self.assertEqual(messages[1].message, "Fout bij het importeren voor locatie Amstel 1: 'Misschien' is not a valid boolean")