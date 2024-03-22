from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models.query import QuerySet

class LocationQuerySet(QuerySet):

    def search_filter(self, params: dict, user: User)-> QuerySet:
        """
        Returns a queryset of locations based on params in a http request.
        """

        from locations.processors import LocationProcessor
        from locations.models import LocationProperty

        # Get request parameters
        property_value = params.get('property', '')
        # Get existing location and external service properties, filtered by access permission
        location_properties = LocationProcessor(user=user).location_properties
        # Set the correct search name when filtering on location property with a choice list
        is_choice_property = LocationProperty.objects.filter(short_name=property_value, property_type='CHOICE').exists()
        if property_value in location_properties and is_choice_property:
            search_name = property_value
        else:
            search_name = 'search'
        search_value = params.get(search_name, '').strip()
        archive_value = params.get('archive', '')

        # Build a Q filter for querying the database 
        # Filter when querying for a specific property
        # Default is full text search when no existing property is queried
        match property_value:
            # Filter on Location.name
            case 'naam':
                qfilter = Q(name__icontains=search_value)
            # Filter on Location.pandcode
            case 'pandcode' if search_value.isdigit():
                qfilter = Q(pandcode=search_value)
            case property_value if property_value:
                # Filter LocationProperty or ExternalService by short_name
                qfilter = (
                    Q(locationdata__location_property__short_name=property_value) |
                    Q(locationexternalservice__external_service__short_name=property_value))
                # If the property is of the CHOICE type
                if is_choice_property:
                    # Filter PropertyOption on option value
                    qfilter &= Q(locationdata___property_option__option=search_value)
                else:
                    # Filter on LocationData or LocationExternalService value
                    qfilter &= (
                        Q(locationdata___value__icontains=search_value) |
                        Q(locationexternalservice__external_location_code__icontains=search_value))
            case _:
                # Do a full search on all tables containing location data
                qfilter = (
                    Q(name__icontains=search_value) |
                    Q(locationdata___value__icontains=search_value) |
                    Q(locationexternalservice__external_location_code__icontains=search_value) |
                    Q(locationdata___property_option__option__icontains=search_value))

        # Filter on location archive attribute; default is only active locations
        match archive_value:
            case 'active':
                qfilter &= Q(is_archived=False)
            case 'archived':
                qfilter &= Q(is_archived=True)
            case 'all':...
            case _:
                qfilter &= Q(is_archived=False)

        # If a user is not authenticated, filter for active locations and public properties only
        if not user.is_authenticated:
            qfilter &= (
                Q(is_archived=False) &
                Q(locationdata__location_property__short_name__in=location_properties) &
                Q(locationexternalservice__external_service__short_name__in=location_properties))

        return self.filter(qfilter).distinct()

