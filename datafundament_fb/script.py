import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datafundament_fb.settings")
django.setup()


from locations.processors import *

value = input("Pancode: ")

location = LocationDataProcessor({
    'building_code': value,
    'name': 'Amstel' + value,
    'description': 'Stadhuis',
    'active': True,
    'street': 'Amstel',
    'street_number': 1,
    'postal_code': '1000 AA',
    'city': 'Amsterdam',
    'Ambtenaren huisvesting': 'Ja',
    'Soort locatie': 'Kantoor',
    'Locatieteam': '1',
    'Gewenste Cat. dienstverlenings kader': '1',
    'Categorie Dienstverleningskader': 'Basis',
    'Budget verantwoordelijke directie': 'Facilitair Bureau',
    'Adres validatie': 'Ja',
    'Locatiemanager': 'Pee Pastinakel',
    'Contactpersoon vanuit Directies': 'Kweetal',
})

breakpoint()


location.save()

get = LocationDataProcessor.get(building_code=value)



print('END')