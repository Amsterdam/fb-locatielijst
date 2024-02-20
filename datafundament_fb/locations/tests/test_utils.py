from django.test import TestCase
from locations.templatetags.utils import get_type

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

