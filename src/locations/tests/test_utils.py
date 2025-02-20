from django.test import Client, TestCase

from locations.models import Location
from locations.templatetags.utils import get_order, get_type, reverse_url, verbose_name


class LocationUtilsTest(TestCase):
    """
    Test Utils
    """

    def test_get_type(self):
        """Test get_type filter"""
        list = ["A", "B", "C"]
        string = "ABC"
        dict = {"1": "a"}

        self.assertEqual(get_type(list), "list")
        self.assertEqual(get_type(string), "str")
        self.assertEqual(get_type(dict), "dict")
        self.assertEqual(get_type(None), "NoneType")

    def test_verbose_name(self):
        """Test returning the verbose name of a model"""

        # Test single name
        self.assertEqual(verbose_name(Location), "Locatie")
        # Test plural name
        self.assertEqual(verbose_name(Location, True), "Locaties")

    def test_reverse_url(self):
        """Test reverse url path from instance"""

        # Test list view and empty view
        self.assertEqual(reverse_url(Location, "list"), "locations_urls:location-list")
        self.assertEqual(reverse_url(Location, ""), "locations_urls:location-")

    def test_get_order(self):
        client = Client()

        # Test default ordering
        request = client.get("/").wsgi_request
        self.assertEqual(get_order(request, "name"), "asc")
        self.assertEqual(get_order(request, "pandcode"), "")

        # Test order parameter
        request = client.get("/?order=desc").wsgi_request
        self.assertEqual(get_order(request, "name"), "desc")
        self.assertEqual(get_order(request, "pandcode"), "")

        # Test order_by parameter
        request = client.get("/?order_by=pandcode").wsgi_request
        self.assertEqual(get_order(request, "pandcode"), "asc")
        self.assertEqual(get_order(request, "name"), "")

        request = client.get("/?order_by=name").wsgi_request
        self.assertEqual(get_order(request, "pandcode"), "")
        self.assertEqual(get_order(request, "name"), "asc")

        # Test order_by and order parameter
        request = client.get("/?order_by=pandcode&order=desc").wsgi_request
        self.assertEqual(get_order(request, "pandcode"), "desc")
        self.assertEqual(get_order(request, "name"), "")

        request = client.get("/?order_by=name&order=desc").wsgi_request
        self.assertEqual(get_order(request, "pandcode"), "")
        self.assertEqual(get_order(request, "name"), "desc")
