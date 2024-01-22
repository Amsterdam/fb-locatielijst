import csv
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.core.files.base import ContentFile
from django.test import TestCase
from django.urls import reverse
from locations.models import Location, LocationProperty, LocationData, PropertyOption


class LocationListViewTest(TestCase):
    """
    Tests for requesting a list of locations
    """

    def setUp(self) -> None:
        self.location = Location.objects.create(pandcode=25000, name='Stopera')
    
    def test_get_view(self):
        """Test requesting the LocationListView"""
        # Request the location list page
        response = self.client.get(reverse('location-list'))
        self.assertEqual(response.status_code, 200)
        # Verify if the correct template is used
        self.assertTemplateUsed(response, 'locations/location-list.html')


class LocationDetailViewTest(TestCase):
    """
    Tests for requesting the detail page of a location
    """

    def setUp(self) -> None:
        self.location = Location.objects.create(pandcode=25000, name='Stopera')
        self.private_property = LocationProperty.objects.create(
            short_name='private', label='Private property', property_type='INT', required=True)
        self.public_property = LocationProperty.objects.create(
            short_name='public', label='Public property', property_type='INT', required=True, public=True)
        self.private_data = LocationData.objects.create(
            location=self.location, location_property=self.private_property, value='Private')
        self.public_data = LocationData.objects.create(
            location=self.location, location_property=self.public_property, value='Public')

    def test_get_view_anonyous(self):
        """Test getting the Location Detail View as an anonymous visitor"""
        
        self.client.force_login(User.objects.get_or_create(username='testuser', is_superuser=True, is_staff=True)[0])
        # Request location detail page
        response = self.client.get(reverse('location-detail', args=[self.location.pandcode]))
        # Verify the response
        self.assertEqual(response.status_code, 200)
        # Verify the response values for the location
        self.assertTemplateUsed(response, 'locations/location-detail.html')
        self.assertEqual(response.context['location_data']['naam'], self.location.name)
        self.assertEqual(response.context['location_data']['pandcode'], self.location.pandcode)
        self.assertIsNotNone(response.context['location_data']['gewijzigd'])
        self.assertEqual(response.context['location_data']['public'], self.public_data.value)

    def test_get_view_authenticated(self):
        """Test getting the Location Detail View as an authenticaed user"""
        # Force login of an authenticated user
        self.client.force_login(User.objects.get_or_create(username='testuser', is_superuser=True, is_staff=True)[0])
        # Request location detail page
        response = self.client.get(reverse('location-detail', args=[self.location.pandcode]))
        # Verify the response
        self.assertEqual(response.status_code, 200)
        # Verify the response values for the location
        self.assertTemplateUsed(response, 'locations/location-detail.html')
        self.assertEqual(response.context['location_data']['naam'], self.location.name)
        self.assertEqual(response.context['location_data']['pandcode'], self.location.pandcode)
        self.assertIsNotNone(response.context['location_data']['gewijzigd'])
        self.assertEqual(response.context['location_data']['private'], self.private_data.value)
        self.assertEqual(response.context['location_data']['public'], self.public_data.value)


class LocationCreateViewTest(TestCase):
    """
    Test creating a new location
    """

    def setUp(self) -> None:
        self.client.force_login(User.objects.get_or_create(username='testuser', is_superuser=True, is_staff=True)[0])
        Location.objects.create(pandcode=24000, name='GGD')
        self.location = Location.objects.create(pandcode=25000, name='Stopera')
        self.integer_property = LocationProperty.objects.create(
            short_name='property', label='property', property_type='INT', required=True, public=True)
        self.location_data = LocationData.objects.create(
            location=self.location, location_property=self.integer_property, value='10')
    
    def test_get_view_anonymous(self):
        """Test getting the location create page"""
        # Log out the user
        self.client.logout()
        # Requesting the page
        response = self.client.get(reverse('location-create'))
        # Verify the response
        self.assertEqual(response.status_code, 302)
        url = reverse('admin:login') + '?next=' + reverse('location-create')
        self.assertEqual(response.url, url)

    def test_get_view_authenticated(self):
        """Test getting the location create page"""
        # Requesting the page
        response = self.client.get(reverse('location-create'))
        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'locations/location-create.html')
        field_names = [item for item in response.context['form'].fields.keys()]
        self.assertListEqual(['naam', self.integer_property.short_name], field_names)
        
    def test_post_view(self):
        """Test posting the create form"""

        # Data for the form        
        data = {'naam': 'Amstel 1', 'property': '10'}
        url = reverse('location-create')
        # Request the post for the form
        response = self.client.post(path=url, data=data)
        
        # Verify the response
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('location-detail', args=[self.location.pandcode + 1]))

        # Verify the redirection from the response
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        # Verify the response values for the location after redirection
        self.assertTemplateUsed(response, 'locations/location-detail.html')
        self.assertEqual(response.context['location_data']['naam'], data['naam'])
        self.assertEqual(response.context['location_data']['pandcode'], self.location.pandcode + 1)
        self.assertIsNotNone(response.context['location_data']['gewijzigd'])

        # Verify the response messages
        messages = [msg for msg in get_messages(response.wsgi_request)]
        self.assertEqual(messages[0].tags, 'success')
        self.assertEqual(messages[0].message, 'De locatie is toegevoegd')

    def test_post_view_invalid_form(self):
        """Test posting a form with invalid values"""
        # Setting malformed data
        data = {'naam': 'Amstel 1', 'property': 'Fout'}
        url = reverse('location-create')
        # Posting the create form
        response = self.client.post(path=url, data=data)
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
        self.assertTemplateUsed(response, 'locations/location-create.html')

        # Verify the response messages
        messages = [msg for msg in get_messages(response.wsgi_request)]
        self.assertEqual(messages[0].tags, 'error')
        self.assertEqual(messages[0].message, 'Niet alle velden zijn juist ingevuld')


    def test_post_view_validation_error(self):
        """Test posting when a validation error occurs in LocationProcessor"""
        # Setting the same name as an existing location
        data = {'naam': 'GGD', 'property': '10'}
        url = reverse('location-create')
        # Posting the create form
        response = self.client.post(path=url, data=data)
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].is_valid())
        self.assertTemplateUsed(response, 'locations/location-create.html')

        # Verify the response messages
        messages = [msg for msg in get_messages(response.wsgi_request)]
        self.assertEqual(messages[0].tags, 'error')
        self.assertEqual(
            messages[0].message,
            "Fout bij het aanmaken van de locatie: {'name': ['Er bestaat al een Locatie met eenzelfde Naam.']}"
        )


class LocationUpdateViewTest(TestCase):
    """
    Test for updating existing locations
    """

    def setUp(self) -> None:
        self.client.force_login(User.objects.get_or_create(username='testuser', is_superuser=True, is_staff=True)[0])
        Location.objects.create(pandcode=24000, name='GGD')
        self.location = Location.objects.create(pandcode=25000, name='Stopera')
        self.integer_property = LocationProperty.objects.create(
            short_name='property', label='property', property_type='INT', required=True)
        self.location_data = LocationData.objects.create(
            location=self.location, location_property=self.integer_property, value='10')

    def test_get_view_anonymous(self):
        """Test getting the location update page as an anonymous user"""
        # Log out the user
        self.client.logout()
        # Requesting the page
        response = self.client.get(reverse('location-update', args=[self.location.pandcode]))
        # Verify the response
        self.assertEqual(response.status_code, 302)
        url = reverse('admin:login') + '?next=' + reverse('location-update', args=[self.location.pandcode])
        self.assertEqual(response.url, url)

    def test_get_view_authenticated(self):
        """Test getting the location update page as an authenticated user"""
        # Requesting the page
        response = self.client.get(reverse('location-update', args=[self.location.pandcode]))
        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'locations/location-update.html')
        field_names = [item for item in response.context['form'].fields.keys()]
        self.assertListEqual(['naam', self.integer_property.short_name], field_names)

    def test_post_view(self):
        """Test posting the update form"""
        # Data for the form 
        data = {'naam': 'Amstel 1', 'property': '10'}
        url = reverse('location-update', args=[self.location.pandcode])
        # Request the post for the form
        response = self.client.post(path=url, data=data)
        # Verify the response
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('location-detail', args=[self.location.pandcode]))

        # Verify the response values for the location after redirection
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'locations/location-detail.html')
        self.assertEqual(response.context['location_data']['naam'], data['naam'])
        self.assertEqual(response.context['location_data']['pandcode'], self.location.pandcode)
        self.assertIsNotNone(response.context['location_data']['gewijzigd'])

        # Verify the response messages
        messages = [msg for msg in get_messages(response.wsgi_request)]
        self.assertEqual(messages[0].tags, 'success')
        self.assertEqual(messages[0].message, 'De locatie is opgeslagen')

    def test_post_view_invalid_form(self):
        """Test posting a form with invalid values"""
        # Setting malformed data
        data = {'naam': 'Stopera', 'property': 'Fout'}
        url = reverse('location-update', args=[self.location.pandcode])
        # Posting the update form
        response = self.client.post(path=url, data=data)
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
        self.assertTemplateUsed(response, 'locations/location-update.html')

        # Verify the response messages
        messages = [msg for msg in get_messages(response.wsgi_request)]
        self.assertEqual(messages[0].tags, 'error')
        self.assertEqual(messages[0].message, 'Niet alle velden zijn juist ingevuld')
        self.assertContains(response, 'is not a valid number')

    def test_post_view_validation_error(self):
        """Test posting when a validation error occurs in LocationProcessor"""
        # Setting the same name as an existing location
        data = {'naam': 'GGD', 'property': '10'}
        url = reverse('location-update', args=[self.location.pandcode])
        # Posting the update form
        response = self.client.post(path=url, data=data)
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].is_valid())
        self.assertTemplateUsed(response, 'locations/location-update.html')

        # Verify the response messages
        messages = [msg for msg in get_messages(response.wsgi_request)]
        self.assertEqual(messages[0].tags, 'error')
        self.assertEqual(
            messages[0].message,
            "Fout bij het updaten van de locatie: {'name': ['Er bestaat al een Locatie met eenzelfde Naam.']}"
        )


class TestLocationImportForm(TestCase):
    """
    Test importing / updating locations by uploading a csv file
    """
    def setUp(self) -> None:
        self.client.force_login(User.objects.get_or_create(username='testuser', is_superuser=True, is_staff=True)[0])
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


class TestLocationExportForm(TestCase):
    """
    Test exporting locations to a csv file for download
    """

    def setUp(self) -> None:
        self.location = Location.objects.create(pandcode=25000, name='Stopera')
        self.boolean_property = LocationProperty.objects.create(
            short_name='occupied', label='occupied', property_type='BOOL', required=True, public=True)
        self.date_property = LocationProperty.objects.create(
            short_name='build', label='build_year', property_type='DATE', required=True, public=True)
        self.email_property = LocationProperty.objects.create(
            short_name='mail', label='mail_address', property_type='EMAIL', required=True, public=True)
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
        self.occupied = LocationData.objects.create(
            location=self.location,
            location_property=self.boolean_property,
            value = 'Ja')
        self.build = LocationData.objects.create(
            location=self.location,
            location_property=self.date_property,
            value = '31-12-2023')
        self.mail = LocationData.objects.create(
            location=self.location,
            location_property=self.email_property,
            value = 'mail@example.org')
        self.floors = LocationData.objects.create(
            location=self.location,
            location_property=self.integer_property,
            value = '10')
        self.note = LocationData.objects.create(
            location=self.location,
            location_property=self.memo_property,
            value = 'Memo')
        self.postcode = LocationData.objects.create(
            location=self.location,
            location_property=self.postal_code_property,
            value = '1234 AB')
        self.color = LocationData.objects.create(
            location=self.location,
            location_property=self.string_property,
            value = 'Tekst')
        self.url = LocationData.objects.create(
            location=self.location,
            location_property=self.url_property,
            value = 'https://example.org')
        self.type = LocationData.objects.create(
            location=self.location,
            location_property=self.choice_property,
            property_option = self.choice_option)

    def test_get_form(self):
        """ Test requesting the csv export page"""
        # Request the download form
        response = self.client.get(reverse('location-export'))
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'locations/location-export.html')
        self.assertContains(response, 'Exporteer Locaties naar CSV')

    def test_post_form_anonymous(self):
        """ Test requesting the csv as an anonymous user; less fields should be in the csv"""
        # Request the csv export
        response = self.client.post(reverse('location-export'), {})

        # Verify the response
        content = response.content
        # Check for the BOM
        self.assertEqual(content[0:3], b'\xef\xbb\xbf')
        
        # Create a csv dictionary from the list and read the first row 
        data = content.decode('utf-8-sig').splitlines()
        csv_dict = csv.DictReader(data)
        row = next(csv_dict)
        
        # Verify the row values
        self.assertEqual(row['pandcode'], str(self.location.pandcode))
        self.assertEqual(row['naam'], self.location.name)
        self.assertEqual(row['occupied'], self.occupied.value)
        self.assertEqual(row['build'], self.build.value)
        self.assertEqual(row['mail'], self.mail.value)
        # Verify that floors is not included in the result
        self.assertNotIn('floors', row)

    def test_post_form_authenticated(self):
        """ Test requesting the csv as an authenticated user; all fields should be in the csv"""        
        # Request the csv export as an authenticated user
        self.client.force_login(User.objects.get_or_create(username='testuser', is_superuser=True, is_staff=True)[0])
        response = self.client.post(reverse('location-export'), {})

        # Verify the response
        content = response.content
        # Check for the BOM
        self.assertEqual(content[0:3], b'\xef\xbb\xbf')
        
        # Create a csv dictionary from the list and read the first row 
        data = content.decode('utf-8-sig').splitlines()
        csv_dict = csv.DictReader(data)
        row = next(csv_dict)
        
        # Verify the row values
        self.assertEqual(row['pandcode'], str(self.location.pandcode))
        self.assertEqual(row['naam'], self.location.name)
        self.assertEqual(row['occupied'], self.occupied.value)
        self.assertEqual(row['build'], self.build.value)
        self.assertEqual(row['mail'], self.mail.value)
        self.assertEqual(row['floors'], self.floors.value)
        self.assertEqual(row['note'], self.note.value)
        self.assertEqual(row['postcode'], self.postcode.value)
        self.assertEqual(row['color'], self.color.value)
        self.assertEqual(row['url'], self.url.value)
        self.assertEqual(row['type'], self.type.property_option.option)

