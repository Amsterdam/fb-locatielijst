from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models.query import QuerySet
from locations.filters import filter_on_archive

class LocationQuerySet(QuerySet):

    def search_filter(self, params: dict, user: User)-> QuerySet:
        """
        Returns a queryset of locations based on params in a http request.
        """

        from locations.processors import LocationProcessor
        from locations.models import LocationProperty

        # Get request parameters
        property_value = params.get('property', '')
        # Get existing location and external service properties for which the requesting user has access to
        accessible_properties = LocationProcessor().location_properties
        # Set the correct search name when filtering on location property with a choice list
        is_choice_property = LocationProperty.objects.filter(short_name=property_value, property_type='CHOICE').exists()
        if property_value in accessible_properties and is_choice_property:
            search_name = property_value
        else:
            search_name = 'search'
        search_value = params.get(search_name, '').strip()
        archive_value = params.get('archive', '')

        # Build a Q filter for querying the database 
        # Filter when querying for a specific property
        # Filter for property fields which the user has access to 
        # Default is full text search when no specific property is queried
        match property_value:
            # Filter on Location.name
            case 'naam':
                qfilter = Q(name__icontains=search_value)
            # Filter on Location.pandcode
            case 'pandcode' if search_value.isdigit():
                qfilter = Q(pandcode=search_value)
            # Filter on a specific location property
            case property_value if property_value:
                if is_choice_property:
                    # Filter for search term and permitted properties in choice lists
                    qfilter = (
                        Q(locationdata___property_option__option=search_value) &
                        Q(locationdata__location_property__short_name__in=accessible_properties)
                    )
                else:
                    qfilter = (
                        # Filter for search term and permitted properties in location properties and external services
                        (
                            Q(locationdata___value__icontains=search_value) &
                            Q(locationdata__location_property__short_name=property_value) &
                            Q(locationdata__location_property__short_name__in=accessible_properties)
                        ) |
                        (
                            Q(locationexternalservice__external_location_code__icontains=search_value) &
                            Q(locationexternalservice__external_service__short_name=property_value) &
                            Q(locationexternalservice__external_service__short_name__in=accessible_properties)
                        )
                    )
            # Do a full search on all tables containing location data               
            case _:
                qfilter = (
                    Q(name__icontains=search_value) |
                    (
                        Q(locationdata___value__icontains=search_value) &
                        Q(locationdata__location_property__short_name__in=accessible_properties)                        
                    ) |
                    (
                        Q(locationdata___property_option__option__icontains=search_value) &
                        Q(locationdata__location_property__short_name__in=accessible_properties)
                    ) |
                    (
                        Q(locationexternalservice__external_location_code__icontains=search_value) &
                        Q(locationexternalservice__external_service__short_name__in=accessible_properties)
                    )
                )
                # When the search_value is an int, we can search in pandcode as well
                if search_value.isdigit():
                    qfilter |= Q(pandcode=search_value)

        # Filter if archive value
        qfilter &= filter_on_archive(archive_value)

        # Filter the results for non authentiated (public) users
        if not user.is_authenticated:
            # Show only active locations
            qfilter &=  Q(is_archived=False)

        return self.filter(qfilter).distinct()

    def archive_filter(self, archive: str= '')-> QuerySet:
        # Filter on location archive attribute; default is only active locations
        qfilter = filter_on_archive(archive)
        return self.filter(qfilter)

