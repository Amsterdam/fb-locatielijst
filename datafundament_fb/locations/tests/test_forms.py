from django import forms
from django.test import TestCase
from locations.forms import LocationImportForm


class TestLocationImportForm(TestCase):
    def setUp(self) -> None:
        return super().setUp()
    
    