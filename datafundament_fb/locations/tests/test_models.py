from django.test import TestCase
from locations.models import compute_building_code, validate_postal_code, Location
from django.core.exceptions import ValidationError


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

    def test_postal_code_validation(self):
        """
        Test  postal code validation
        """

        # Test the validator
        self.location1.postal_code = '1234 AA'
        self.assertEqual(validate_postal_code(self.location1.postal_code), self.location1.postal_code)

        # Test for validation errors
        # No space between the numbers and letters
        self.location1.postal_code = '1234AA'
        self.assertRaises(ValidationError, self.location1.full_clean)

        # Only one letter
        self.location1.postal_code = '1234 A'
        self.assertRaises(ValidationError, self.location1.full_clean)

        # Only 3 numbers
        self.location1.postal_code = '123 AA'
        self.assertRaises(ValidationError, self.location1.full_clean)

        # Letters in lower case
        self.location1.postal_code = '1234 aa'
        self.assertRaises(ValidationError, self.location1.full_clean)

        # Leading with a zero
        self.location1.postal_code = '0234 AA'
        self.assertRaises(ValidationError, self.location1.full_clean)

        # Prohibited combination of letters (SA, SD, SS)
        self.location1.postal_code = '1234 SS'
        self.assertRaises(ValidationError, self.location1.full_clean)