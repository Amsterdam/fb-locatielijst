from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from help_docs.models import Documentation


# Create your tests here.
class TestDocumentation(TestCase):
    fixtures = ["documentations"]

    def setUp(self) -> None:
        self.client.force_login(User.objects.get_or_create(username="testuser", is_superuser=True, is_staff=True)[0])

    def test_documentation(self):
        # get documentation instance id
        documentation_id = Documentation.objects.first().id

        # list page
        response = self.client.get(reverse("help_docs_urls:documentation-list"))
        self.assertEqual(response.status_code, 200)

        # detail page
        response = self.client.get(reverse("help_docs_urls:documentation-detail", args=[documentation_id]))
        self.assertEqual(response.status_code, 200)

    def test_documentation_unauthorized(self):
        """Check if the form is only accessible for staff members"""
        # Ceate user with withou staff permissions
        self.client.force_login(User.objects.get_or_create(username="no_admin")[0])

        # get documentation instance id
        documentation_id = Documentation.objects.first().id

        # verify that access is not allowed and request is redirect to login page
        # list page
        url = reverse("help_docs_urls:documentation-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/admin/login/?next=" + url)

        # detail page
        url = reverse("help_docs_urls:documentation-detail", args=[documentation_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/admin/login/?next=" + url)


class TestReorderObjects(TestCase):
    def setUp(self) -> None:
        self.documentation_one = Documentation(title="one", description="One", body="Content", order=1)
        self.documentation_two = Documentation(title="two", description="Two", body="Content", order=1)
        self.documentation_three = Documentation(title="three", description="Three", body="Content", order=2)

    def test_post_save_reordening(self):
        # Save the first documentation
        self.documentation_one.save()
        # Order should be at 1
        self.assertEqual(Documentation.objects.filter(title="one").first().order, 1)

        # Save the second documentation
        self.documentation_two.save()
        # Order should be at 1
        self.assertEqual(Documentation.objects.filter(title="two").first().order, 1)
        # Order of the first documentation should be at two
        self.assertEqual(Documentation.objects.filter(title="one").first().order, 2)

        # Save the thid documentation without any order
        self.documentation_three.save()
        # The property should be last in order
        self.assertEqual(Documentation.objects.all().order_by("order").last().order, 3)
