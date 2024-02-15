from django.test import TestCase
from django.contrib.auth.models import User
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
        response = self.client.get('/docs/')
        self.assertEqual(response.status_code, 200)
        # verify links block is overridden by the custom template
        self.assertIn('<a href="/docs/">Documentation</a>', str(response.content))
        # verify list template; title and description
        self.assertIn('<li><a href="/docs/1/">{doc_title}</a> | {doc_desc}</li>'.format(doc_title=documentation.title, doc_desc=documentation.description), str(response.content))

        # detail page
        response = self.client.get('/docs/1/')
        self.assertEqual(response.status_code, 200)
        # verify links block is overridden by the custom template
        self.assertIn('<a href="/docs/">Documentation</a>', str(response.content))
        # verify template content; title and body (the first 25 characters)
        self.assertIn('<h1>{doc_title}</h1>'.format(doc_title=documentation.title), str(response.content))
        self.assertIn(documentation.body[1:25], str(response.content))

    def test_documentation_unauthorized(self):
        """Check if the form is only accessible for staff members"""
        # Ceate user with withou staff permissions
        self.client.force_login(User.objects.get_or_create(username='no_admin')[0])

        # verify that access is not allowed and request is redirect to login page
        # list page
        response = self.client.get('/docs/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/login/?next=/docs/')

        # detail page
        response = self.client.get('/docs/1/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/login/?next=/docs/1/')  
    