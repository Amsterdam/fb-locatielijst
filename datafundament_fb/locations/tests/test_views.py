import csv
from unittest.mock import patch, PropertyMock
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.messages import get_messages
from django.core.files.base import ContentFile
from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse
from parameterized import parameterized
from locations.models import Location, LocationProperty, LocationData, PropertyOption, ExternalService
from locations.processors import LocationProcessor
from locations.signals import disconnect_signals
from locations.views import get_csv_file_response


class LocationListView(TestCase):
    """
    Tests for searching in the list of locations
    """
    def setUp(self) -> None:
        # Disable signals called for log events
        disconnect_signals()
        self.authenticated_user = User.objects.create(username='testuser', is_superuser=False, is_staff=True)
        self.anonymous_user = AnonymousUser()
        LocationProperty.objects.create(
            short_name='public', label='Public property', property_type='STR', public=True)
        LocationProperty.objects.create(
            short_name='private', label='Private property', property_type='STR', public=False)
        choice_property = LocationProperty.objects.create(
            short_name='choice', label='choice property', property_type='CHOICE', public=True)
        PropertyOption.objects.create(
            location_property=choice_property, option='KeuzeOptie1')
        PropertyOption.objects.create(
            location_property=choice_property, option='KeuzeOptie2')
        ExternalService.objects.create(
            name='External service', short_name='external', public=True)
        Location.objects.create(
            pandcode=24001, name='Stadhuis', is_archived=False)
        Location.objects.create(
            pandcode=24002, name='Stopera', is_archived=False)
        Location.objects.create(
            pandcode=24003, name='Ambtswoning', is_archived=True )
        LocationProcessor(user=self.authenticated_user, data={
            'pandcode': '24001',
            'naam': 'Stadhuis',
            'public': 'Publiek',
            'private': 'Prive',
            'choice': 'KeuzeOptie1',
            'external': '10042',
        }).save()
        LocationProcessor(user=self.authenticated_user, data={
            'pandcode': '24002',
            'naam': 'Stopera',
            'public': 'Publiek',
            'private': 'Geheim',
            'choice': 'KeuzeOptie2',
            'external': '20042',
        }).save()
        LocationProcessor(user=self.authenticated_user, data={
            'pandcode': '24003',
            'naam': 'Ambtswoning',
            'public': 'Burgemeester',
            'private': 'Prive',
            'choice': 'KeuzeOptie1',
            'external': '30042',
        }).save()

    @parameterized.expand([
            # Search all fields
            ('', '', False, '', [24001, 24002]),
            ('keuze', '', False, '', [24001, 24002]),
            ('prive', '', False, '', []),
            ('0042', '', False, '', [24001, 24002]),
            ('10042', '', False, '', [24001]),
            ('prive', '', True, '', [24001]),
            # Search name
            ('adhuis', 'naam', False, '', [24001]),
            ('wonin', 'naam', False, '', []),
            ('opera', 'naam', True, '', [24002]),
            # Search pandcode
            ('24002', 'pandcode', False, '', [24002]),
            ('24003', 'pandcode', False, '', []),
            ('24003', 'pandcode', True, 'all', [24003]),
            # Search public property
            ('publiek', 'public', False, '', [24001, 24002]),
            ('meester', 'public', True, 'all', [24003]),
            # Search private property
            ('prive', 'private', False, '', []),
            ('prive', 'private', True, 'all', [24001, 24003]),
            # Search choice property
            ('KeuzeOptie1', 'choice', False, '', [24001]),
            ('KeuzeOptie1', 'choice', True, 'all', [24001, 24003]),
            ('KeuzeOptie2', 'choice', False, '', [24002]),
            ('optie', 'choice', False, '', []),
            ('', 'choice', True, 'all', []),
            # Search external service location code
            ('10042', 'external', False, '', [24001]),
            ('30042', 'external', False, '', []),
            ('30042', 'external', True, 'all', [24003]),
            # Archive property for (non)authenticated users
            ('', '', False, '', [24001, 24002]),
            ('', '', False, 'active', [24001, 24002]),
            ('', '', False, 'archived', []),
            ('', '', False, 'all', [24001, 24002]),
            ('', '', True, '', [24001, 24002]),
            ('', '', True, 'active', [24001, 24002]),
            ('', '', True, 'archived', [24003]),
            ('', '', True, 'all', [24001, 24002, 24003]),
    ])
    def test_search(self, search, location_property, is_authenticated, archive, expected):
        """
        Paramaterized test where the following combinations of conditions are tested:
        Authenticated/Anonymous user
        Archived/Active/All locations
        Search in all location properties
        Search in public location properties
        Search in private location properties
        Search in fixed choice list properties
        """
      
        # Set params for the locations search filter 
        params = { 
            'property': location_property,
            'archive': archive,
        }

        # Set the correct user
        if is_authenticated:
            user = self.authenticated_user
        else:
            user = self.anonymous_user

        # Set the name for the parameter holding the searchvalue to the property name if it is location_property and a choice list
        location_properties = LocationProcessor(user=user).location_properties
        is_choice_property = LocationProperty.objects.filter(short_name=location_property, property_type='CHOICE').exists()
        if location_property in location_properties and is_choice_property:
            params[location_property] = search
        else:
            params['search'] = search

        # Call the filter for the request
        locations = Location.objects.search_filter(params, user)
        pandcodes = set(locations.values_list('pandcode', flat=True))
        # Compare the filtered locations against expected locations
        self.assertEqual(pandcodes, set(expected))
        # Check for distinct results
        self.assertEqual(len(locations), len(expected))
    
    def test_get_view(self):
        """Test requesting the LocationListView"""
        # Request the location list page
        response = self.client.get(reverse('locations_urls:location-list'))
        self.assertEqual(response.status_code, 200)
        # Verify if the correct template is used
        self.assertTemplateUsed(response, 'locations/location-list.html')


class LocationDetailViewTest(TestCase):
    """
    Tests for requesting the detail page of a location
    """

    def setUp(self) -> None:
        # Disable signals called for log events
        disconnect_signals()
        self.client.force_login(User.objects.get_or_create(username='testuser', is_superuser=True, is_staff=True)[0])
        self.location = Location.objects.create(pandcode=25000, name='Stopera')
        self.private_property = LocationProperty.objects.create(
            short_name='private', label='Private property', property_type='NUM', required=True)
        self.public_property = LocationProperty.objects.create(
            short_name='public', label='Public property', property_type='NUM', required=True, public=True)
        self.private_data = LocationData.objects.create(
            location=self.location, location_property=self.private_property, value='Private')
        self.public_data = LocationData.objects.create(
            location=self.location, location_property=self.public_property, value='Public')
        self.multichoice_property = LocationProperty.objects.create(
            short_name='multi', label='teams', property_type='CHOICE', multiple=True)
        self.multichoice_option1 = PropertyOption.objects.create(
            location_property=self.multichoice_property, option='Team 1')
        self.multichoice_option2 = PropertyOption.objects.create(
            location_property=self.multichoice_property, option='Team 2')
        self.location_data_option1 = LocationData.objects.create(
            location=self.location, location_property=self.multichoice_property, _property_option=self.multichoice_option1)
        self.location_data_option2 = LocationData.objects.create(
            location=self.location, location_property=self.multichoice_property, _property_option=self.multichoice_option2)

    def test_get_view_anonymous(self):
        """Test getting the Location Detail View as an anonymous visitor"""
        # Log out the user
        self.client.logout()
        # Request location detail page
        response = self.client.get(reverse('locations_urls:location-detail', args=[self.location.pandcode]))
        # Verify the response
        self.assertEqual(response.status_code, 200)
        # Verify the response values for the location
        self.assertTemplateUsed(response, 'locations/location-detail.html')
        self.assertEqual(response.context['location_data']['naam'], self.location.name)
        self.assertEqual(response.context['location_data']['pandcode'], self.location.pandcode)
        self.assertIsNotNone(response.context['location_data']['gewijzigd'])
        self.assertEqual(response.context['location_data']['public'], self.public_data.value)
        self.assertIsNone(response.context['location_data'].get('private'))

    def test_get_view_authenticated(self):
        """
        Test getting the Location Detail View as an authenticated user,
        including a multiple choice location property
        """
        # Request location detail page
        response = self.client.get(reverse('locations_urls:location-detail', args=[self.location.pandcode]))
        # Verify the response
        self.assertEqual(response.status_code, 200)
        # Verify the response values for the location
        self.assertTemplateUsed(response, 'locations/location-detail.html')
        self.assertEqual(response.context['location_data']['naam'], self.location.name)
        self.assertEqual(response.context['location_data']['pandcode'], self.location.pandcode)
        self.assertIsNotNone(response.context['location_data']['gewijzigd'])
        self.assertEqual(response.context['location_data']['private'], self.private_data.value)
        self.assertEqual(response.context['location_data']['public'], self.public_data.value)
        # Verify the response values for the multiple choice location_data
        value = [self.multichoice_option1.option, self.multichoice_option2.option]
        self.assertEqual(response.context['location_data']['multi'], value)

    def test_post_view_to_archive(self):
        """Test getting the Location Detail View as an anonymous visitor"""
        # Verifiy that the location is not archived
        location = Location.objects.get(pandcode=self.location.pandcode)
        self.assertFalse(location.is_archived)

        # Post to the location detail page to archive the location
        url = reverse('locations_urls:location-detail', args=[self.location.pandcode])
        data = {'_archive': ['archive'],}
        response = self.client.post(path=url, data=data)

        # Verify the response
        self.assertEqual(response.status_code, 302)
        url = reverse('locations_urls:location-detail', args=[self.location.pandcode])
        self.assertEqual(response.url, url)

        # Verify that the location is archived now
        location.refresh_from_db()
        self.assertTrue(location.is_archived)

        # Post to the location detail page to de-archive the location
        url = reverse('locations_urls:location-detail', args=[self.location.pandcode])
        data = {'_archive': ['dearchive'],}
        response = self.client.post(path=url, data=data)

        # Verify that the location is archived now
        location.refresh_from_db()
        self.assertFalse(location.is_archived)

    def test_post_view_to_archive_anonymous(self):
        # Log out the user
        self.client.logout()
        """Test getting the Location Detail View as an anonymous visitor"""
        # Verifiy that the location is not archived
        location = Location.objects.get(pandcode=self.location.pandcode)
        self.assertFalse(location.is_archived)

        # Post to the location detail page
        url = reverse('locations_urls:location-detail', args=[self.location.pandcode])
        data = {'_archive': ['archive'],}
        response = self.client.post(path=url, data=data)

        # Verify the response
        self.assertEqual(response.status_code, 302)
        url = reverse('admin:login') + '?next=' + reverse('locations_urls:location-detail', args=[self.location.pandcode])
        self.assertEqual(response.url, url)

        # Verify that the location is not archived
        location.refresh_from_db()
        self.assertFalse(location.is_archived)

class LocationCreateViewTest(TestCase):
    """
    Test creating a new location
    """

    def setUp(self) -> None:
        # Disable signals called for log events
        disconnect_signals()
        self.client.force_login(User.objects.get_or_create(username='testuser', is_superuser=True, is_staff=True)[0])
        Location.objects.create(pandcode=24000, name='GGD')
        self.location = Location.objects.create(pandcode=25000, name='Stopera')
        self.number_property = LocationProperty.objects.create(
            short_name='property', label='property', property_type='NUM', required=True, public=True)
        self.location_data = LocationData.objects.create(
            location=self.location, location_property=self.number_property, value='10')
        self.multichoice_property = LocationProperty.objects.create(
            short_name='multitype', label='teams', property_type='CHOICE', multiple=True)
        self.multichoice_option1 = PropertyOption.objects.create(
            location_property=self.multichoice_property, option='Team 1')
        self.multichoice_option2 = PropertyOption.objects.create(
            location_property=self.multichoice_property, option='Team 2')
        self.location_data_option1 = LocationData.objects.create(
            location=self.location, location_property=self.multichoice_property, _property_option=self.multichoice_option1)
        self.location_data_option2 = LocationData.objects.create(
            location=self.location, location_property=self.multichoice_property, _property_option=self.multichoice_option2)

    def test_get_view_anonymous(self):
        """Test getting the location create page"""
        # Log out the user
        self.client.logout()
        # Requesting the page
        response = self.client.get(reverse('locations_urls:location-create'))
        # Verify the response
        self.assertEqual(response.status_code, 302)
        url = reverse('admin:login') + '?next=' + reverse('locations_urls:location-create')
        self.assertEqual(response.url, url)

    def test_get_view_authenticated(self):
        """Test getting the location create page"""
        # Requesting the page
        response = self.client.get(reverse('locations_urls:location-create'))
        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'locations/location-create.html')
        field_names = [item for item in response.context['form'].fields.keys()]
        location_data_names = ['naam', self.number_property.short_name, self.multichoice_property.short_name, ]
        self.assertListEqual(location_data_names, field_names)
        
    def test_post_view(self):
        """Test posting the create form"""

        # Data for the form        
        data = {'naam': 'Amstel 1', 'property': '10', 'multitype': ['Team 1', 'Team 2']}
        url = reverse('locations_urls:location-create')
        # Request the post for the form
        response = self.client.post(path=url, data=data)
        
        # Verify the response
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('locations_urls:location-detail', args=[self.location.pandcode + 1]))

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
        self.assertEqual(messages[0].message, 'De locatie is toegevoegd.')

    def test_post_view_invalid_form(self):
        """Test posting a form with invalid values"""
        # Setting malformed data
        data = {'naam': 'Amstel 1', 'property': 'Fout'}
        url = reverse('locations_urls:location-create')
        # Posting the create form
        response = self.client.post(path=url, data=data)
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
        self.assertTemplateUsed(response, 'locations/location-create.html')

        # Verify the response messages
        messages = [msg for msg in get_messages(response.wsgi_request)]
        self.assertEqual(messages[0].tags, 'error')
        self.assertEqual(messages[0].message, 'Niet alle velden zijn juist ingevuld.')

    def test_post_view_validation_error(self):
        """Test posting when a validation error occurs in LocationProcessor"""
        # Setting the same name as an existing location
        data = {'naam': 'GGD', 'property': '10'}
        url = reverse('locations_urls:location-create')
        # Posting the create form
        response = self.client.post(path=url, data=data)
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
        self.assertTemplateUsed(response, 'locations/location-create.html')

        # Verify the response messages
        messages = [msg for msg in get_messages(response.wsgi_request)]
        self.assertEqual(messages[0].tags, 'error')
        self.assertEqual(
            messages[0].message,
            "Niet alle velden zijn juist ingevuld."
        )

        # Verify the form error
        form_errors = response.context['form'].errors
        self.assertEqual(form_errors['naam'][0], f"Er bestaat al een locatie met de naam '{data['naam']}'.")


class LocationUpdateViewTest(TestCase):
    """
    Test for updating existing locations
    """

    def setUp(self) -> None:
        # Disable signals called for log events
        disconnect_signals()
        self.client.force_login(User.objects.get_or_create(username='testuser', is_superuser=True, is_staff=True)[0])
        Location.objects.create(pandcode=24000, name='GGD')
        self.location = Location.objects.create(pandcode=25000, name='Stopera')
        self.number_property = LocationProperty.objects.create(
            short_name='property', label='property', property_type='NUM', required=True)
        self.location_data = LocationData.objects.create(
            location=self.location, location_property=self.number_property, value='10')
        self.multichoice_property = LocationProperty.objects.create(
            short_name='multi', label='teams', property_type='CHOICE', multiple=True)
        self.multichoice_option1 = PropertyOption.objects.create(
            location_property=self.multichoice_property, option='Team 1')
        self.multichoice_option2 = PropertyOption.objects.create(
            location_property=self.multichoice_property, option='Team 2')
        self.location_data_option1 = LocationData.objects.create(
            location=self.location, location_property=self.multichoice_property, _property_option=self.multichoice_option1)
        self.location_data_option2 = LocationData.objects.create(
            location=self.location, location_property=self.multichoice_property, _property_option=self.multichoice_option2)

    def test_get_view_anonymous(self):
        """Test getting the location update page as an anonymous user"""
        # Log out the user
        self.client.logout()
        # Requesting the page
        response = self.client.get(reverse('locations_urls:location-update', args=[self.location.pandcode]))
        # Verify the response
        self.assertEqual(response.status_code, 302)
        url = reverse('admin:login') + '?next=' + reverse('locations_urls:location-update', args=[self.location.pandcode])
        self.assertEqual(response.url, url)

    def test_get_view_authenticated(self):
        """Test getting the location update page as an authenticated user"""
        # Requesting the page
        response = self.client.get(reverse('locations_urls:location-update', args=[self.location.pandcode]))
        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'locations/location-update.html')
        field_names = [item for item in response.context['form'].fields.keys()]
        location_data_names = ['naam',  self.number_property.short_name, self.multichoice_property.short_name, ]
        self.assertListEqual(location_data_names, field_names)

    def test_post_view(self):
        """Test posting the update form"""
        # Data for the form
        data = {'naam': 'Stopera', 'property': '11', 'multi': ['Team 1']}
        url = reverse('locations_urls:location-update', args=[self.location.pandcode])
        # Request the post for the form
        response = self.client.post(path=url, data=data)
        # Verify the response
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('locations_urls:location-detail', args=[self.location.pandcode]))

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
        self.assertEqual(messages[0].message, 'De locatie is opgeslagen.')

    def test_post_view_invalid_form(self):
        """Test posting a form with invalid values"""
        # Setting malformed data
        data = {'naam': 'Stopera', 'property': 'Fout'}
        url = reverse('locations_urls:location-update', args=[self.location.pandcode])
        # Posting the update form
        response = self.client.post(path=url, data=data)
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
        self.assertTemplateUsed(response, 'locations/location-update.html')

        # Verify the response messages
        messages = [msg for msg in get_messages(response.wsgi_request)]
        self.assertEqual(messages[0].tags, 'error')
        self.assertEqual(messages[0].message, 'Niet alle velden zijn juist ingevuld.')
        self.assertContains(response, 'is geen geldig getal.')

    def test_post_view_validation_error(self):
        """Test posting when a validation error occurs in LocationProcessor"""
        # Setting the same name as an existing location (case insensitive)
        data = {'naam': 'ggd', 'property': '10'}
        url = reverse('locations_urls:location-update', args=[self.location.pandcode])
        # Posting the update form
        response = self.client.post(path=url, data=data)
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
        self.assertTemplateUsed(response, 'locations/location-update.html')

        # Verify the response messages
        messages = [msg for msg in get_messages(response.wsgi_request)]
        self.assertEqual(messages[0].tags, 'error')
        self.assertEqual(
            messages[0].message,
            "Niet alle velden zijn juist ingevuld."
        )

        # Verify the form error
        form_errors = response.context['form'].errors
        self.assertEqual(form_errors['naam'][0], f"Er bestaat al een locatie met de naam '{data['naam']}'.")


class TestLocationImportForm(TestCase):
    """
    Test importing / updating locations by uploading a csv file
    """
    def setUp(self) -> None:
        # Disable signals called for log events
        disconnect_signals()
        self.client.force_login(User.objects.get_or_create(username='testuser', is_superuser=True, is_staff=True)[0])
        self.location = Location.objects.create(pandcode='25000', name='Stopera')
        self.boolean_property = LocationProperty.objects.create(
            short_name='bool', label='Boolean', property_type='BOOL')
        self.date_property = LocationProperty.objects.create(
            short_name='date', label='Date', property_type='DATE')
        self.email_property = LocationProperty.objects.create(
            short_name='mail', label='Email', property_type='EMAIL')
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
        self.choice_option_ = PropertyOption.objects.create(
            location_property=self.choice_property, option='Oranges|Apples')
        self.multichoice_property = LocationProperty.objects.create(
            short_name='multi', label='teams', property_type='CHOICE', multiple=True)
        self.multichoice_option1 = PropertyOption.objects.create(
            location_property=self.multichoice_property, option='Team 1')
        self.multichoice_option2 = PropertyOption.objects.create(
            location_property=self.multichoice_property, option='Team 2')
        self.csv_content  = [
            'pandcode;naam;bool;date;mail;num;memo;post;str;url;choice;multi',
            '25001;Amstel 1;Ja;31-12-2023;mail@example.org;99;Memo tekst;1234AB;Tekst;https://example.org;"Oranges|Apples";Team 1|Team 2'
        ]

    def test_import_csv_get(self):
        """Get the form"""
        response = self.client.get(reverse('locations_urls:location-import'))

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'locations/location-import.html')
        self.assertIn('Locaties importeren', str(response.content))

    def test_import_csv_post(self):
        """Post the form"""
        csv_file = ContentFile('\n'.join(self.csv_content).encode(), name='import-file.csv')
        data = {'csv_file': csv_file}
        url = reverse('locations_urls:location-import')
        response = self.client.post(url, data)

        # Verify response
        self.assertEqual(response.status_code, 200)

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
        headers = self.csv_content[0].split(';')
        self.assertEqual(set(used_columns), set(headers))

        # Success message
        self.assertEqual(messages[1].message, f"Locatie Amstel 1 is geïmporteerd/ge-update.")

        # Verify that the location instance exists
        location = Location.objects.get(pandcode=25001)
        self.assertEqual(location.name, 'Amstel 1')
        # Including the location from the setup() there should be 2 locations now
        self.assertEqual(Location.objects.all().count(), 2)

    def test_import_csv_post_invalid_file(self):
        """Post the form with an invalid file extension"""
        xslx_file = ContentFile('\n'.join(self.csv_content).encode(), name='import-file.xlsx')
        data = {'csv_file': xslx_file}
        url = reverse('locations_urls:location-import')
        response = self.client.post(url, data)

        # Verify response
        self.assertEqual(response.status_code, 200)

        # Verify response message
        messages = [msg for msg in get_messages(response.wsgi_request)]
        self.assertEqual(messages[0].tags, 'error')
        self.assertEqual(messages[0].message, "import-file.xlsx is geen gelding CSV bestand.")

    def test_import_csv_post_invalid_value(self):
        """Post the form with an invalid form value"""
        # CSV data
        csv_content = [
            'pandcode;naam;bool;date;mail;num;memo;post;str;url;choice',
            '25001;Amstel 1;Misschien;31-12-2023;mail@example.org;99;Memo tekst;1234AB;Tekst;https://example.org;Yellow'
        ]
        csv_file = ContentFile('\n'.join(csv_content).encode(), name='import-file.csv')
        data = {'csv_file': csv_file}
        url = reverse('locations_urls:location-import')
        response = self.client.post(url, data)

        # Verify response
        self.assertEqual(response.status_code, 200)

        # Verify response message
        messages = [msg for msg in get_messages(response.wsgi_request)]
        self.assertEqual(messages[1].tags, 'error')
        self.assertEqual(messages[1].message, "Fout bij het importeren voor locatie Amstel 1: [\"'Misschien' is geen geldige boolean.\", \"'Yellow' is geen geldige invoer voor Choice.\"]")


    def test_import_csv_wrong_delimiter(self):
        """ Test csv import when the delimiter is not set to semicolin """
        csv_content = [
            'pandcode,naam,bool,date,mail,num,memo,post,str,url,choice',
            '25001,Amstel 1,Ja,31-12-2023,mail@example.org,99,Memo tekst,1234AB,Tekst,https://example.org,Orange'
        ]
        csv_file = ContentFile('\n'.join(csv_content).encode(), name='import-file.csv')
        data = {'csv_file': csv_file}
        url = reverse('locations_urls:location-import')
        response = self.client.post(url, data)

        # Verify response
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], reverse('locations_urls:location-import'))  

        # Verify response message
        messages = [msg for msg in get_messages(response.wsgi_request)]
        self.assertEqual(messages[0].tags, 'error')
        self.assertEqual(messages[0].message, "De locaties kunnen niet ingelezen worden. Zorg ervoor dat je ';' als scheidingsteken en UTF-8 als codering gebruikt.")

    def test_import_csv_with_excess_columns(self):
        """ Test csv import when a data row has more columns than the header; for instance when a value has a semicolon"""
        csv_content = [
            'pandcode;naam;bool;date;mail;num;memo;post;str;url;choice',
            '25001;Amstel 1;Ja;31-12-2023;mail@example.org;99;Memo tekst;1234AB;Tekst;https://example.org;;Yellow'
        ]
        csv_file = ContentFile('\n'.join(csv_content).encode(), name='import-file.csv')
        data = {'csv_file': csv_file}
        url = reverse('locations_urls:location-import')
        response = self.client.post(url, data)

        # Verify response
        self.assertEqual(response.status_code, 200)

        # Verify response message
        messages = [msg for msg in get_messages(response.wsgi_request)]
        self.assertEqual(messages[1].tags, 'warning')
        self.assertEqual(messages[1].message, "Rij 1 is niet verwerkt want deze heeft teveel kolommen")

        # There should be only one location from the setup()
        self.assertEqual(Location.objects.all().count(), 1)

    def test_import_csv_with_missing_columns(self):
        """ Test csv import when a data row has less columns than the header"""
        csv_content = [
            'pandcode;naam;bool;date;mail;num;memo;post;str;url;choice',
            '25001;Amstel 1;Ja;31-12-2023;mail@example.org;99;Memo tekst;1234AB;Tekst;https://example.org'
        ]
        csv_file = ContentFile('\n'.join(csv_content).encode(), name='import-file.csv')
        data = {'csv_file': csv_file}
        url = reverse('locations_urls:location-import')
        response = self.client.post(url, data)

        # Verify response
        self.assertEqual(response.status_code, 200)

        # Verify response message
        messages = [msg for msg in get_messages(response.wsgi_request)]
        self.assertEqual(messages[1].tags, 'warning')
        self.assertEqual(messages[1].message, "Rij 1 is niet verwerkt want deze mist een kolom")

        # There should be only one location from the setup()
        self.assertEqual(Location.objects.all().count(), 1)


class TestLocationExport(TestCase):
    """
    Test exporting locations to a csv file for download
    """

    def setUp(self) -> None:
        # Disable signals called for log events
        disconnect_signals()
        self.location = Location.objects.create(pandcode=25000, name='Stopera')
        self.boolean_property = LocationProperty.objects.create(
            short_name='occupied', label='occupied', property_type='BOOL', required=True, public=True)
        self.date_property = LocationProperty.objects.create(
            short_name='build', label='build_year', property_type='DATE', required=True, public=True)
        self.email_property = LocationProperty.objects.create(
            short_name='mail', label='mail_address', property_type='EMAIL', required=True, public=True)
        self.number_property = LocationProperty.objects.create(
            short_name='floors', label='number_of_floors', property_type='NUM', required=True)
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
        self.multichoice_property = LocationProperty.objects.create(
            short_name='multi', label='teams', property_type='CHOICE', multiple=True)
        self.multichoice_option1 = PropertyOption.objects.create(
            location_property=self.multichoice_property, option='Team 1')
        self.multichoice_option2 = PropertyOption.objects.create(
            location_property=self.multichoice_property, option='Team 2')
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
            location_property=self.number_property,
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
            _property_option = self.choice_option)
        self.location_data_option1 = LocationData.objects.create(
            location=self.location,
            location_property=self.multichoice_property,
            _property_option=self.multichoice_option1)
        self.location_data_option2 = LocationData.objects.create(
            location=self.location,
            location_property=self.multichoice_property,
            _property_option=self.multichoice_option2)
        self.user = User.objects.create(username='testuser', is_superuser=False, is_staff=True)

    def test_get_form(self):
        """ Test requesting the csv export page"""
        # Request the download form
        response = self.client.get(reverse('locations_urls:location-export'))
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'locations/location-export.html')
        self.assertContains(response, 'Exporteer Locaties naar CSV')

    def test_get_form_filtered(self):
        """ Test requesting the csv export page with query parameters"""
        # Request the download form with a random query parameter 
        response = self.client.get(reverse('locations_urls:location-export') + "?param=value")

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('Content-Type'), 'text/csv, charset=utf-8')

    def test_post_form(self):
        """ Test posting to the the csv export page"""
        # Request the download form with a random query parameter 
        response = self.client.post(reverse('locations_urls:location-export'), {})

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('Content-Type'), 'text/csv, charset=utf-8')

    def test_get_csv_file_response_anonymous(self):
        """ Test getting the csv http response object as an anonymous user"""
        # Request the csv file http response
        request = HttpRequest()
        request.user = AnonymousUser()
        locations = Location.objects.all()
        # Call the function to get the csv file reponse
        response = get_csv_file_response(request=request, locations=locations)

        # Verify the response
        content = response.content
        # Check for the BOM
        self.assertEqual(content[0:3], b'\xef\xbb\xbf')
        
        # Create a csv dictionary from the list and read the first row 
        data = content.decode('utf-8-sig').splitlines()
        # Set the dialect for the csv by sniffing the first line
        csv_dialect = csv.Sniffer().sniff(sample=data[0], delimiters=';')
        csv_dict = csv.DictReader(data, dialect=csv_dialect)
        row = next(csv_dict)
        
        # Verify the row values
        self.assertEqual(row['pandcode'], str(self.location.pandcode))
        self.assertEqual(row['naam'], self.location.name)
        self.assertEqual(row['occupied'], self.occupied.value)
        self.assertEqual(row['build'], self.build.value)
        self.assertEqual(row['mail'], self.mail.value)
        # Verify that floors is not included in the result
        self.assertNotIn('floors', row)

    def test_get_csv_file_response_authenticated(self):
        """ Test getting the csv http response as an authenticated user; all fields should be in the csv"""        
        # Request the csv file http response
        request = HttpRequest()
        request.user = self.user
        locations = Location.objects.all()
        # Call the function to get the csv file reponse
        response = get_csv_file_response(request=request, locations=locations)

        # Verify the response
        content = response.content
        # Check for the BOM
        self.assertEqual(content[0:3], b'\xef\xbb\xbf')
        
        # Create a csv dictionary from the list and read the first row 
        data = content.decode('utf-8-sig').splitlines()
        # Set the dialect for the csv by sniffing the first line
        csv_dialect = csv.Sniffer().sniff(sample=data[0], delimiters=';')
        csv_dict = csv.DictReader(data, dialect=csv_dialect)
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
        self.assertEqual(row['type'], self.type._property_option.option)
        self.assertEqual(row['multi'], str(self.multichoice_option1.option) + '|' + str(self.multichoice_option2.option))

    def test_csv_with_headers_only(self):
        """ Test requesting an empty csv, with only headers, when there are no locations in the database"""        
        # Empty the database firts
        Location.objects.all().delete()

        # Request the csv file http response
        request = HttpRequest()
        request.user = self.user
        locations = Location.objects.all()
        # Call the function to get the csv file reponse
        response = get_csv_file_response(request=request, locations=locations)

        # Verify the response
        content = response.content
        
        # Create a csv dictionary from the list and read the first row 
        data = content.decode('utf-8-sig').splitlines()
        # Set the dialect for the csv by sniffing the first line
        csv_dialect = csv.Sniffer().sniff(sample=data[0], delimiters=';')
        csv_dict = csv.DictReader(data, dialect=csv_dialect)
        
        # Verify the headers
        headers = set(csv_dict.fieldnames)
        properties = {'color', 'url', 'multi', 'build', 'postcode', 'pandcode', 'note', 'type', 'mail', 'occupied', 'floors', 'naam'}
        self.assertEqual(headers, properties)

        # Verify that there are no rows in the csv
        i = 0
        for row in csv_dict:
            i += 1
        self.assertEqual(i, 0)


class TestLocationAdminView(TestCase):
    """
    Tests for the LocationAdminView
    """
    def setUp(self) -> None:
        # Disable signals called for log events
        disconnect_signals()
        self.client.force_login(User.objects.get_or_create(username='testuser', is_superuser=True, is_staff=True)[0])

    def test_get_view_authenticated(self):
        """Test requesting the view as an authenticated user"""
        # Request the location admin page
        response = self.client.get(reverse('location-admin'))
        self.assertEqual(response.status_code, 200)
        # Verify if the correct template is used
        self.assertTemplateUsed(response, 'locations/location-admin.html')

    def test_get_view_anonymous(self):
        """Test getting the location admin page as an anonymous user"""
        # Log out the user
        self.client.logout()
        # Requesting the page
        response = self.client.get(reverse('location-admin'))
        # Verify the response
        self.assertEqual(response.status_code, 302)
        url = reverse('admin:login') + '?next=' + reverse('location-admin')
        self.assertEqual(response.url, url)


class TestListViewPaginator(TestCase):
    fixtures = [
        'locations',
        'property_groups',
        'location_properties',
        'property_options',
        'location_data',
        'external_services',
        'location_external_services',
    ]

    @patch('locations.views.LocationListView.paginate_by', new_callable=PropertyMock)
    def test_page_pop(self, mock):
        """Test to verify if the page parameter is ommitted from the export url"""
        # Set pagination to 1 result per page to invoke pagination
        mock.return_value = '1'
        # Call the location list view

        response = self.client.get(reverse('locations_urls:location-list') + '?page=2')
        # Verify the response
        self.assertEqual(response.status_code, 200)
        # Assert 1 result per page
        self.assertEqual(len(response.context['object_list']), 1)
        # Query variable should not contain the parameter page
        self.assertEqual(response.context['query'], '')
        # Verify that the mock attribute is called
        self.assertTrue(mock.called)

