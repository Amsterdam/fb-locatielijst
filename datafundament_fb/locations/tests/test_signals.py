from django.contrib.auth.models import User
from django.test import TestCase
from locations.models import Location, LocationData, LocationProperty, PropertyOption, ExternalService, LocationExternalService, PropertyGroup, Log
from locations.signals import disconnect_signals, connect_signals
from shared.middleware import current_user

class TestReorderObjects(TestCase):
    def setUp(self) -> None:
        # Disable signals called for log events
        disconnect_signals()
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


class TestLogging(TestCase):
    """
    Test logging events
    """

    def setUp(self) -> None:
        # Make sure signals are connected
        connect_signals()
        self.user = User.objects.create(username='testuser', is_superuser=False, is_staff=True)
        self.location = Location(pandcode=24001, name='Stadhuis', is_archived=False,)
        self.location_property = LocationProperty(
            short_name='property', label='Locatie eigenschap', property_type='STR', public=True,)
        self.property_option = PropertyOption(
            location_property=self.location_property, option='Optie',)
        self.external_service = ExternalService(
            name='Externe service', short_name='service', public=True,)
        self.location_data = LocationData(
            location=self.location, location_property=self.location_property, _value='Tekst')
        self.location_external_service = LocationExternalService(
            location=self.location, external_service=self.external_service, external_location_code='Code', 
        )
        # set current user 
        current_user.set(self.user)
    
    def test_property_create_log(self):
        """
        Test log when creating new Locationdata and LocationExternalService instances
        """
        self.location.save()
        self.location_property.save()
        self.external_service.save()
        
        # Test LocationData
        self.location_data.save()
        # Check resulting log. Should be the first in the queryset
        log = Log.objects.all().first()
        self.assertEqual(log.model, self.location)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.target, self.location_property.label)
        message = 'Waarde ({value}) gezet.'.format(value=self.location_data.value)
        self.assertEqual(log.message, message)
 
        # LocationExternalService
        self.location_external_service.save()
        # Check resulting log. Should be the first in the queryset
        log = Log.objects.all().first()
        self.assertEqual(log.model, self.location)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.target, self.external_service.name)
        message = 'Waarde ({value}) gezet.'.format(value=self.location_external_service.external_location_code)
        self.assertEqual(log.message, message)

    def test_property_change_log(self):
        """
        Test log when modifying existing Locationdata and LocationExternalService
        """
        self.location.save()
        self.location_property.save()
        self.external_service.save()
        
        # Test LocationData
        self.location_data.save()
        # Change value
        old_value = self.location_data.value
        new_value = 'Een andere tekst'
        self.location_data.value = new_value
        self.location_data.save()
        # Check resulting log. Should be the first in the queryset
        log = Log.objects.all().first()
        self.assertEqual(log.model, self.location)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.target, self.location_property.label)
        message = f"Waarde was ({old_value}), is gewijzigd naar ({new_value})."
        self.assertEqual(log.message, message)

        # LocationExternalService
        self.location_external_service.save()
        # Change value
        old_value = self.location_external_service.external_location_code
        new_value = 'Andere code'
        self.location_external_service.external_location_code = new_value
        self.location_external_service.save()
        # Check resulting log. Should be the first in the queryset
        log = Log.objects.all().first()
        self.assertEqual(log.model, self.location)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.target, self.external_service.name)
        message = f"Waarde was ({old_value}), is gewijzigd naar ({new_value})."
        self.assertEqual(log.message, message)

    def test_property_delete_log(self):
        """
        Test log when deleting Locationdata instances
        """
        self.location.save()
        self.location_property.save()
        self.external_service.save()
        self.location_data.save()
        
        # Delete the LocationData
        self.location_data.delete()
        # Check resulting log. Should be the first in the queryset
        log = Log.objects.all().first()
        self.assertEqual(log.model, self.location)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.target, self.location_property.label)
        message = 'Waarde ({value}) verwijderd.'.format(value=self.location_data.value)
        self.assertEqual(log.message, message)

    def test_model_create_log(self):
        """
        Test log when creating ExternalService, PropertyOption, LocationProperty and Location instances
        """
        instances = [self.location, self.location_property, self.property_option, self.external_service]
        for instance in instances:
            # Save the instance
            instance.save()
            # Check resulting log. Should be the first in the queryset
            log = Log.objects.all().first()
            self.assertIsNone(log.model)
            self.assertEqual(log.user, self.user)
            self.assertEqual(log.target, instance._meta.verbose_name)
            self.assertEqual(log.message, f"{instance} is aangemaakt.")

    def test_model_change_log(self):
        """
        Test log when creating ExternalService, PropertyOption, LocationProperty and Location instances
        """
        params = [
            (self.location, 'pandcode', '20001'),
            (self.location_property, 'multiple', True),
            (self.property_option, 'option', 'Andere optie'),
            (self.external_service, 'name', 'Andere service')
        ]
        for param in params:
            instance = param[0]
            attribute = param[1]
            new_value = param[2]
            old_value = getattr(param[0], param[1])
            
            # Save the instance
            instance.save()
            # Change a value
            setattr(instance, attribute, new_value)
            # Save the instance
            instance.save()
            
            # Check resulting log. Should be the first in the queryset
            log = Log.objects.all().first()
            self.assertEqual(log.model, instance)
            self.assertEqual(log.user, self.user)
            self.assertEqual(log.target, instance._meta.get_field(attribute).verbose_name)
            message = f"Waarde was ({old_value}), is gewijzigd naar ({new_value})."
            self.assertEqual(log.message, message)

    def test_model_delete_log(self):
        """
        Test logging delete events for for ExternalService, PropertyOption, LocationProperty and Location
        """
        instances = [self.location, self.location_property, self.external_service]
        for instance in instances:
            # Save the instance
            instance.save()
            # Delete the instance
            instance.delete()
            # Check resulting log. Should be the first in the queryset
            log = Log.objects.all().first()
            self.assertIsNone(log.model)
            self.assertEqual(log.user, self.user)
            self.assertEqual(log.target, instance._meta.verbose_name)
            self.assertEqual(log.message, f"{instance} is verwijderd.")

        # Testing PropertyOption seperately because of dependen on LocationProperty
        # Save the instance
        self.location_property.save()
        self.property_option.save()
        # Delete the instance
        self.property_option.delete()
        # Check resulting log. Should be the first in the queryset
        log = Log.objects.all().first()
        self.assertIsNone(log.model)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.target, self.property_option._meta.verbose_name)
        self.assertEqual(log.message, f"{self.property_option} is verwijderd.")
