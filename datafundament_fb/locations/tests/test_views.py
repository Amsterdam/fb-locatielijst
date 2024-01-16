from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from locations.models import Location

class LocationListViewTest(TestCase):

    def setUp(self) -> None:
        self.location = Location.objects.create(pandcode=25000, name='Stopera')
    
    def test_get_view(self):
        response = self.client.get(reverse('location-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'locations/location-list.html')


class LocationDetailViewTest(TestCase):

    def setUp(self) -> None:
        self.location = Location.objects.create(pandcode=25000, name='Stopera')
    
    def test_get_view(self):
        response = self.client.get(reverse('location-detail', args=[self.location.pandcode]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'locations/location-detail.html')
        self.assertEqual(response.context['location_data']['naam'], self.location.name)
        self.assertEqual(response.context['location_data']['pandcode'], self.location.pandcode)
        self.assertIsNotNone(response.context['location_data']['gewijzigd'])


class LocationCreateViewTest(TestCase):

    def setUp(self) -> None:
        self.location = Location.objects.create(pandcode=25000, name='Stopera')
    
    def test_get_view(self):
        response = self.client.get(reverse('location-create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'locations/location-create.html')

    def test_post_view(self):
        data = {'naam': 'Amstel 1'}
        url = reverse('location-create')
        response = self.client.post(path=url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('location-detail', args=[self.location.pandcode + 1]))

        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'locations/location-detail.html')
        self.assertEqual(response.context['location_data']['naam'], data['naam'])
        self.assertEqual(response.context['location_data']['pandcode'], self.location.pandcode + 1)
        self.assertIsNotNone(response.context['location_data']['gewijzigd'])

        messages = [msg for msg in get_messages(response.wsgi_request)]
        self.assertEqual(messages[0].tags, 'success')
        self.assertEqual(messages[0].message, 'De locatie is toegevoegd')

    def test_post_view_invalid_form(self):
        data = {'naam': ''}
        url = reverse('location-create')
        response = self.client.post(path=url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
        self.assertTemplateUsed(response, 'locations/location-create.html')


class LocationUpdateViewTest(TestCase):

    def setUp(self) -> None:
        self.location = Location.objects.create(pandcode=25000, name='Stopera')

    def test_get_view(self):
        response = self.client.get(reverse('location-update', args=[self.location.pandcode]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'locations/location-update.html')

    def test_post_view(self):
        data = {'naam': 'Amstel 1'}
        url = reverse('location-update', args=[self.location.pandcode])
        response = self.client.post(path=url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('location-detail', args=[self.location.pandcode]))

        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'locations/location-detail.html')
        self.assertEqual(response.context['location_data']['naam'], self.location.name)
        self.assertEqual(response.context['location_data']['pandcode'], self.location.pandcode)
        self.assertIsNotNone(response.context['location_data']['gewijzigd'])

        messages = [msg for msg in get_messages(response.wsgi_request)]
        self.assertEqual(messages[0].tags, 'success')
        self.assertEqual(messages[0].message, 'De locatie is opgeslagen')

    def test_post_view_invalid_form(self):
        data = {'naam': ''}
        url = reverse('location-update', args=[self.location.pandcode])
        response = self.client.post(path=url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
        self.assertTemplateUsed(response, 'locations/location-update.html')