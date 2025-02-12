from django.db.models import Manager
from locations.querysets import LocationQuerySet


class LocationManager(Manager.from_queryset(LocationQuerySet)):...

