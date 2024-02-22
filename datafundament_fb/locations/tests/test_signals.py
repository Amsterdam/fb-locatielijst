from django.test import TestCase
from unittest.mock import patch
from locations.models import LocationProperty, PropertyGroup, ExternalService


class TestReorderObjects(TestCase):
    def setUp(self) -> None:
        self.property_group = PropertyGroup(
            name='group', order=None)
        self.external_service = ExternalService(
            name='Externe service', short_name='ext_srv', order=None)
        self.location_property_one = LocationProperty(
            short_name='one', label='One', property_type='STR', order=1)
        self.location_property_two = LocationProperty(
            short_name='two', label='Two', property_type='STR', order=1)
        self.location_property_three = LocationProperty(
            short_name='three', label='Three', property_type='STR', order=None)
        self.location_property_grouped = LocationProperty(
            short_name='group', label='Grouped property', property_type='STR', order=1, group=self.property_group)

    def test_post_save_reordening(self):
        # Save the property_group instance
        self.property_group.save()
        # Order should be at 1
        self.assertEqual(PropertyGroup.objects.filter(name='group').first().order, 1)

        # Save the external_service instance
        self.external_service.save()
        # Order should be at 1
        self.assertEqual(ExternalService.objects.filter(short_name='ext_srv').first().order, 1)

        # Save the first location_propery
        self.location_property_one.save()
        # Order should be at 1
        self.assertEqual(LocationProperty.objects.filter(short_name='one').first().order, 1)

        # Save the second location_propery
        self.location_property_two.save()
        # Order should be at 1
        self.assertEqual(LocationProperty.objects.filter(short_name='two').first().order, 1)
        # Order of the first location_property should be at two
        self.assertEqual(LocationProperty.objects.filter(short_name='one').first().order, 2)

        # Save the thid location_property without any order
        self.location_property_three.save()
        # The property should be last in order
        self.assertEqual(LocationProperty.objects.all().order_by('order').last().order, 3)

        # Saving the grouped location_property
        self.location_property_grouped.save()
        # Order should be at 1
        self.assertEqual(LocationProperty.objects.filter(short_name='group').first().order, 1)
        # Order of the second location_property should also be at 1
        self.assertEqual(LocationProperty.objects.filter(short_name='two').first().order, 1)

