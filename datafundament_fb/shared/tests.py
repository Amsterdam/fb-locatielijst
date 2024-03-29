from django.contrib.auth.models import User
from django.test import TestCase
from shared.utils import get_log_parameters
from locations.models import Location, LocationData, LocationProperty, PropertyOption, ExternalService, LocationExternalService


# Create your tests here.
class TestSharedUtils(TestCase):
    """
    Test utils in shared app
    """
    
    def setUp(self) -> None:
        user = User.objects.create(username='testuser', is_superuser=False, is_staff=True)
        location = Location.objects.create(pandcode=24001, name='Stadhuis', is_archived=False, last_modified_by=user,)
        location_property = LocationProperty.objects.create(
            short_name='property', label='Location property', property_type='CHOICE', public=True, last_modified_by=user,)
        property_option = PropertyOption.objects.create(
            location_property=location_property, option='Optie', last_modified_by=user,)
        external_service = ExternalService.objects.create(
            name='External service', short_name='service', public=True, last_modified_by=user,)
        location_data = LocationData.objects.create(
            location=location, location_property=location_property, _property_option=property_option, last_modified_by=user,)
        location_external_service = LocationExternalService.objects.create(
            location=location, external_service=external_service, external_location_code='Code', last_modified_by=user, 
        )


    def test_get_log_parameters(self):
        models = [Location, LocationProperty, PropertyOption, LocationData, ExternalService, LocationExternalService]
        # Test Location log objects
        for model in models:
            instance = model.objects.all().first()
            log_parameters = get_log_parameters(instance)
            for obj in log_parameters:
                # Verify that the field exists in the model
                has_attribute = hasattr(model, obj['attribute_name'])
                self.assertTrue(has_attribute)
                self.assertIsNotNone(obj['display_name'])