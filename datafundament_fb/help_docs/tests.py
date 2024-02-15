from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from help_docs.models import Documentation

# Create your tests here.
class TestDocumentation(TestCase):
    fixtures = ['documentations']

    def setUp(self) -> None:
        self.client.force_login(User.objects.get_or_create(username='testuser', is_superuser=True, is_staff=True)[0])
    
    def test_documentation(self):
        # get documentation instance
        documentation = Documentation.objects.get(id=1)

        # list page
        response = self.client.get(reverse('help_docs_urls:documentation-list'))
        self.assertEqual(response.status_code, 200)
        
        # detail page
        response = self.client.get(reverse('help_docs_urls:documentation-detail', args=[1]))
        self.assertEqual(response.status_code, 200)

    def test_documentation_unauthorized(self):
        """Check if the form is only accessible for staff members"""
        # Ceate user with withou staff permissions
        self.client.force_login(User.objects.get_or_create(username='no_admin')[0])

        # verify that access is not allowed and request is redirect to login page
        # list page
        url = reverse('help_docs_urls:documentation-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/admin/login/?next=' + url)

        # detail page
        url = reverse('help_docs_urls:documentation-detail', args=[1])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/admin/login/?next=' + url)
    