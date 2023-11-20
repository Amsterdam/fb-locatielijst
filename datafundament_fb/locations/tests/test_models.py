from django.test import TestCase
from locations.models import compute_building_code, Location



class TestModelFunctions(TestCase):
    """
    Test custom model functions
    """

    def setUp(self) -> None:
        self.location1 = Location(building_code='25000', name='Stopera', description='Stadhuis',
                                 street='Amstel1', street_number=1, postal_code='1000 AA',
                                 city='Amsterdam')
        self.location2 = Location(building_code='24000', name='GGD', description='Gemeentelijke Gezondheidsdienst',
                                street='Nieuw Achtergracht', street_number=100, postal_code='1018 BB',
                                city='Amsterdam')


    def test_compute_building_code(self):
        """
        Test auto compute of the building code in Location based on the current highest number
        """

        # Test when there is no Location object yet in the db
        self.assertEqual(Location.objects.all().count(), 0)
        self.assertEqual(compute_building_code(), 1)

        # Test when there are existing location objects
        self.location1.save()
        self.location2.save()
        location_with_highest_building_code = Location.objects.all().order_by('-building_code').first()
        next_building_code = location_with_highest_building_code.building_code + 1
        self.assertEqual(compute_building_code(), next_building_code)
