from django.test import TestCase
from locations.templatetags.utils import get_type, verbose_name, reverse_url
from locations.models import Location
from django.db import models
class LocationUtilsTest(TestCase):
    """
    Test Utils
    """

    def test_get_type(self):
        """Test get_type filter"""
        list = ['A', 'B', 'C']
        string = 'ABC'
        dict = {'1': 'a'}

        self.assertEqual(get_type(list), 'list')
        self.assertEqual(get_type(string), 'str')
        self.assertEqual(get_type(dict), 'dict')
        self.assertEqual(get_type(None), 'NoneType')

    def test_verbose_name(self):
        """Test returning the verbose name of a model"""

        # Test single name
        self.assertEqual(verbose_name(Location), 'Locatie')
        # Test plural name
        self.assertEqual(verbose_name(Location, True), 'Locaties')

    def test_reverse_url(self):
        """Test reverse url path from instance"""

        # Test list view and empty view
        self.assertEqual(reverse_url(Location, 'list'), 'location-list')
        self.assertEqual(reverse_url(Location, ''), 'location-')