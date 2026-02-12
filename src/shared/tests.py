from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from locations.models import (
    ExternalService,
    Location,
    LocationData,
    LocationExternalService,
    LocationProperty,
    PropertyOption,
)
from shared.context import current_user
from shared.utils import get_log_parameters


# Create your tests here.
class TestSharedUtils(TestCase):
    """
    Test utils in shared app
    """

    def setUp(self) -> None:
        user = User.objects.create(username="testuser", is_superuser=False, is_staff=True)
        # because of CurrentUserMiddleware set current_user to this user
        current_user.set(user)
        location = Location.objects.create(
            pandcode=24001,
            name="Stadhuis",
            is_archived=False,
        )
        location_property = LocationProperty.objects.create(
            short_name="property",
            label="Location property",
            property_type="CHOICE",
            public=True,
        )
        property_option = PropertyOption.objects.create(
            location_property=location_property,
            option="Optie",
        )
        external_service = ExternalService.objects.create(
            name="External service",
            short_name="service",
            public=True,
        )
        LocationData.objects.create(
            location=location,
            location_property=location_property,
            _property_option=property_option,
        )
        LocationExternalService.objects.create(
            location=location,
            external_service=external_service,
            external_location_code="Code",
        )

    def test_get_log_parameters(self):
        models = [Location, LocationProperty, PropertyOption, LocationData, ExternalService, LocationExternalService]
        # Test Location log objects
        for model in models:
            instance = model.objects.all().first()
            log_parameters = get_log_parameters(instance)
            for obj in log_parameters:
                # Verify that the field exists in the model
                has_attribute = hasattr(model, obj["attribute_name"])
                self.assertTrue(has_attribute)
                self.assertIsNotNone(obj["display_name"])


class TestCurrentUserMiddleware(TestCase):
    """
    Test setting a contextvar with the user associated with a request, in case of an authenticated session. Or an
    anonymous user for non authenticated requests.
    """

    def test_is_plain_user(self):
        # Request a page as a plain user
        self.user = User.objects.get_or_create(username="testuser", is_staff=False)[0]
        self.client.force_login(self.user)
        response = self.client.get(reverse("locations_urls:location-list"))
        self.assertEqual(response.context["request"].user, current_user.get())

    def test_anonymous_user(self):
        # Request a page as an anoymous user
        self.client.logout()
        login_url = reverse("login")
        location_url = reverse("locations_urls:location-list")
        response = self.client.get(location_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], f"{login_url}?next={location_url}")
