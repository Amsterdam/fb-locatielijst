from django.test import TestCase
from locations.models import Location, LocationProperty, PropertyOption, LocationData, ExternalService, LocationExternalService

class TestFixtures(TestCase):
    """
    Test to verify that the fixtures still work after, for instance, a migration
    """
    fixtures = [
        'locations',
        'location_properties',
        'property_options',
        'location_data',
        'external_services',
        'location_external_services',
    ]

    def setUp(self) -> None:
        return super().setUp()

    def test_fixtures(self):
        self.assertTrue(Location.objects.all())
        self.assertTrue(LocationProperty.objects.all())
        self.assertTrue(PropertyOption.objects.all())
        self.assertTrue(LocationData.objects.all())
        self.assertTrue(ExternalService.objects.all())
        self.assertTrue(LocationExternalService.objects.all())