from django import forms
from django.utils.safestring import mark_safe

class LocationImportForm(forms.Form):
    """Form to import a CSV file with location data"""
    csv_file = forms.FileField(
        required=True, label='CSV bestand',
        help_text=mark_safe('Kies het locatie bronbestand dat je wilt uploaden.')
    )