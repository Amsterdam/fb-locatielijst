from django.test import TestCase

from locations.models import (
    ExternalService,
    Location,
    LocationData,
    LocationExternalService,
    LocationProperty,
    PropertyOption,
)
from shared.context import set_current_user


class TestFixtures(TestCase):
    """
    Test to verify that the fixtures still work after, for instance, a migration
    """

    fixtures = [
        "locations",
        "property_groups",
        "location_properties",
        "property_options",
        "location_data",
        "external_services",
        "location_external_services",
    ]

    # while loading the fixtures the contextvar current_user should be set to None
    @classmethod
    @set_current_user()
    def setUpClass(cls):
        super().setUpClass()

    def test_fixtures(self):
        self.assertTrue(Location.objects.all())
        self.assertTrue(LocationProperty.objects.all())
        self.assertTrue(PropertyOption.objects.all())
        self.assertTrue(LocationData.objects.all())
        self.assertTrue(ExternalService.objects.all())
        self.assertTrue(LocationExternalService.objects.all())
