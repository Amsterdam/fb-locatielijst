from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models.query import QuerySet
from fblocatie.filters import filter_on_archive

from fblocatie.utils.search_mappings import (
    DEFAULT_TEXT_LOOKUPS,
    DEFAULT_INT_LOOKUPS,
    FOREIGN_KEY_LOOKUPS,
    INT_FIELD_LOOKUPS,
    MANY_TO_MANY_LOOKUPS,
    PERSON_LOOKUP_PREFIXES,
    TEXT_FIELD_LOOKUPS,
)

TRUE_STRINGS = {"ja", "j", "true", "1", "yes", "y"}
FALSE_STRINGS = {"nee", "n", "false", "0", "no"}

def _any_icontains(term: str, lookups: tuple[str, ...]) -> Q:
    q = Q()
    for lookup in lookups:
        q |= Q(**{lookup: term})
    return q

def _person_name_match(term: str, prefix: str) -> Q:
    return (
        Q(**{f"{prefix}__voornaam__icontains": term})
        | Q(**{f"{prefix}__achternaam__icontains": term})
        | Q(**{f"{prefix}__email__icontains": term})
    )

def _extract_search_term(params: dict) -> str:
    return (params.get("search") or "").strip()

class LocatieQuerySet(QuerySet):
    def search_filter(self, params: dict, user: User) -> QuerySet:
        """Return a queryset of locations filtered by search params.

        Query params:
        - `property`: optional, selects a single field to search in
        - `search`: the search term
        - `archive`: active|archived|all (default: active)

        Non-staff users always only see active locations.
        """

        property_value = (params.get("property") or "").strip()
        search_value = _extract_search_term(params)
        archive_value = (params.get("archive") or "").strip()

        qs = self
        qfilter = Q()
        needs_distinct = False

        if search_value:
            if property_value == "":
                qfilter &= _any_icontains(search_value, DEFAULT_TEXT_LOOKUPS)
                if search_value.isdigit():
                    for field in DEFAULT_INT_LOOKUPS:
                        qfilter |= Q(**{field: int(search_value)})
            elif property_value in INT_FIELD_LOOKUPS:
                if not search_value.isdigit():
                    return qs.none()
                qfilter &= Q(**{INT_FIELD_LOOKUPS[property_value]: int(search_value)})
            elif property_value in TEXT_FIELD_LOOKUPS:
                qfilter &= Q(**{TEXT_FIELD_LOOKUPS[property_value]: search_value})
            elif property_value in FOREIGN_KEY_LOOKUPS:
                id_lookup, name_lookup = FOREIGN_KEY_LOOKUPS[property_value]
                qfilter &= Q(**{id_lookup: int(search_value)}) if search_value.isdigit() else Q(**{name_lookup: search_value})
            elif property_value in MANY_TO_MANY_LOOKUPS:
                id_lookup, name_lookup = MANY_TO_MANY_LOOKUPS[property_value]
                needs_distinct = True
                qfilter &= Q(**{id_lookup: int(search_value)}) if search_value.isdigit() else Q(**{name_lookup: search_value})
            elif property_value in PERSON_LOOKUP_PREFIXES:
                needs_distinct = True
                qfilter &= _person_name_match(search_value, PERSON_LOOKUP_PREFIXES[property_value])
            elif property_value in {"vvo", "bvo"}:
                try:
                    val = Decimal(search_value)
                except InvalidOperation:
                    return qs.none()
                qfilter &= Q(**{("vastgoed__vvo" if property_value == "vvo" else "vastgoed__bvo"): val})
            elif property_value == "ambtenaar":
                val = search_value.lower()
                if val in TRUE_STRINGS:
                    qfilter &= Q(ambtenaar=True)
                elif val in FALSE_STRINGS:
                    qfilter &= Q(ambtenaar=False)
                else:
                    return qs.none()
            elif property_value == "adrs_toeg":
                qfilter &= _any_icontains(
                    search_value,
                    (
                        "bezoekadres__straat__icontains",
                        "bezoekadres__postcode__icontains",
                        "bezoekadres__woonplaats__icontains",
                    ),
                )
            elif property_value == "gv_grp":
                qfilter &= _any_icontains(search_value, ("vastgoed__GV_key__icontains", "vastgoed__gv_id__icontains"))
            else:
                return qs.none()

        # Archive filtering
        qfilter &= filter_on_archive(archive_value)

        # Non-staff users only see active locations
        if not user.is_staff:
            qfilter &= Q(archief=False)

        qs = qs.filter(qfilter)
        if needs_distinct:
            qs = qs.distinct()
        return qs

    def archive_filter(self, archive: str = "") -> QuerySet:
        return self.filter(filter_on_archive(archive))
