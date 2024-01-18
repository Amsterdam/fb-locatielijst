from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from locations.models import Location, LocationProperty, LocationData

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
        self.integer_property = LocationProperty.objects.create(
            short_name='property', label='property', property_type='INT', required=True)
        self.location_data = LocationData.objects.create(
            location=self.location, location_property=self.integer_property, value='10')

    def test_get_view(self):
        """Test getting the Location Detail View"""
        # Request location detail page
        response = self.client.get(reverse('location-detail', args=[self.location.pandcode]))
        # Verify the response
        self.assertEqual(response.status_code, 200)
        # Verify the response values for the location
        self.assertTemplateUsed(response, 'locations/location-detail.html')
        self.assertEqual(response.context['location_data']['naam'], self.location.name)
        self.assertEqual(response.context['location_data']['pandcode'], self.location.pandcode)
        self.assertIsNotNone(response.context['location_data']['gewijzigd'])
        self.assertEqual(response.context['location_data']['property'], self.location_data.value)


class LocationCreateViewTest(TestCase):
    """
    Test creating a new location
    """

    def setUp(self) -> None:
        Location.objects.create(pandcode=24000, name='GGD')
        self.location = Location.objects.create(pandcode=25000, name='Stopera')
        self.integer_property = LocationProperty.objects.create(
            short_name='property', label='property', property_type='INT', required=True)
        self.location_data = LocationData.objects.create(
            location=self.location, location_property=self.integer_property, value='10')
    
    def test_get_view(self):
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
            "Fout bij het aanmaken van de locatie: {'name': ['Locatie with this Naam already exists.']}"
        )


class LocationUpdateViewTest(TestCase):

    def setUp(self) -> None:
        Location.objects.create(pandcode=24000, name='GGD')
        self.location = Location.objects.create(pandcode=25000, name='Stopera')
        self.integer_property = LocationProperty.objects.create(
            short_name='property', label='property', property_type='INT', required=True)
        self.location_data = LocationData.objects.create(
            location=self.location, location_property=self.integer_property, value='10')

    def test_get_view(self):
        """Test getting the location update page"""
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
            "Fout bij het updaten van de locatie: {'name': ['Locatie with this Naam already exists.']}"
        )