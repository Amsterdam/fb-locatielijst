from django.test import TestCase
from django.core.management import call_command

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