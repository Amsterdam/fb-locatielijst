from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models.query import QuerySet
from fblocatie.filters import filter_on_archive

YES = {"ja", "j", "true", "1", "yes", "y"}
NO = {"nee", "n", "false", "0", "no"}


def _or(term: str, lookups: tuple[str, ...]) -> Q:
    q = Q()
    for lookup in lookups:
        q |= Q(**{lookup: term})
    return q


def _person(term: str, prefix: str) -> Q:
    return _or(
        term,
        (
            f"{prefix}__voornaam__icontains",
            f"{prefix}__achternaam__icontains",
            f"{prefix}__email__icontains",
        ),
    )


def _int_prefix_ranges(field: str, prefix: str, *, max_digits: int = 10) -> Q:
    """Fast prefix search for integer fields without casting.

    Example: prefix '24' matches 24, 24001, 249999, 2400000000, etc.
    """

    if not prefix.isdigit():
        return Q(pk__in=[])

    base = int(prefix)
    n = len(prefix)
    q = Q()
    for total_digits in range(n, max_digits + 1):
        factor = 10 ** (total_digits - n)
        lower = base * factor
        upper = (base + 1) * factor
        q |= Q(**{f"{field}__gte": lower}) & Q(**{f"{field}__lt": upper})
    return q


def _num(params: dict, prop: str) -> str:
    # We always search using the `search` query param.
    return (params.get("search") or "").strip()


TEXT = {
    "naam": "naam__icontains",
    "afkorting": "afkorting__icontains",
    "beschrving": "beschrijving__icontains",
    "lt_mail": "loc_email__icontains",
    "routecode": "routecode__iexact",
    "straat": "adres__straat__icontains",
    "postcode": "adres__postcode__icontains",
    "huisletter": "adres__huisletter__icontains",
    "numtoeg": "adres__huisnummertoevoeging__icontains",
    "plaats": "adres__woonplaats__icontains",
    "maps": "adres__map_url__icontains",
    "adres2_rol": "bezoekadres_functie__icontains",
    "kantoorart": "kantoorkast__icontains",
    "gv": "vastgoed__GV_key__icontains",
    "energielbl": "vastgoed__energielabel__icontains",
    "mon_gem": "vastgoed__monument_gem__name__icontains",
}

# Default = "Alle tekstvelden" (keep it fast; exclude M2M/person searches)
DEFAULT_LOOKUPS = tuple(sorted({v for k, v in TEXT.items() if k != "routecode"} | {"routecode__icontains"}))

FK = {
    "soort": ("locatie_soort_id", "locatie_soort__name__icontains"),
    "dvk_naam": ("dvk_naam_id", "dvk_naam__name__icontains"),
    "budget_dir": ("budget_dir_id", "budget_dir__name__icontains"),
    "themagv": ("vastgoed__themagv_id", "vastgoed__themagv__name__icontains"),
    "ew": ("perceel_installateur_id", "perceel_installateur__name__icontains"),
    "bezit": ("vastgoed__bezit_id", "vastgoed__bezit__name__icontains"),
    "mon_brkpb": ("vastgoed__monument_brkpb_id", "vastgoed__monument_brkpb__name__icontains"),
}

M2M = {
    "vlekken": ("pand_directies__id", "pand_directies__name__icontains"),
    "voorz": ("voorzieningen__id", "voorzieningen__name__icontains"),
    "contract": ("contracten__id", "contracten__name__icontains"),
}

INT_EXACT = {
    "werkplek": "werkplekken",
    "lt": "locatieteam",
    "huisnummer": "adres__huisnummer",
    "bouwjaar": "vastgoed__bouwjaar",
}

PERSON_PREFIX = {
    "lm": "loc_manager",
    "lc": "loc_coordinator",
    "contact": "contact_dir",
    "tom": "tom",
    "tsc": "tsc",
    "beveiligng": "beveiliging",
    "veiligheid": "veiligheid",
    "am_gv": "vastgoed__asset_manager",
    "plgv": "vastgoed__pl_gv",
}


class LocatieQuerySet(QuerySet):
    def search_filter(self, params: dict, user: User) -> QuerySet:
        """Return a queryset of `Locatie` filtered by search params.

        Query params (mirrors the `locations` app style):
        - `property`: optional, selects a single field to search in
        - `search`: the search term (always used in fblocatie)
        - `archive`: active|archived|all (default: active)

        Non-staff users always only see active locations.
        """

        property_value = (params.get("property") or "").strip()
        search_value = _num(params, property_value)
        archive_value = (params.get("archive") or "").strip()

        qs = self
        qfilter = Q()
        needs_distinct = False

        if search_value:
            if property_value == "":
                qfilter &= _or(search_value, DEFAULT_LOOKUPS)
                if search_value.isdigit():
                    qfilter |= _int_prefix_ranges("pandcode", search_value)
            elif property_value == "pandcode":
                qfilter &= _int_prefix_ranges("pandcode", search_value)
            elif property_value == "ambtenaar":
                val = search_value.lower()
                if val in YES:
                    qfilter &= Q(ambtenaar=True)
                elif val in NO:
                    qfilter &= Q(ambtenaar=False)
                else:
                    return qs.none()
            elif property_value == "adrs_toeg":
                qfilter &= _or(
                    search_value,
                    (
                        "bezoekadres__straat__icontains",
                        "bezoekadres__postcode__icontains",
                        "bezoekadres__woonplaats__icontains",
                    ),
                )
            elif property_value == "gv_grp":
                qfilter &= _or(search_value, ("vastgoed__GV_key__icontains", "vastgoed__gv_id__icontains"))
            elif property_value in INT_EXACT:
                if not search_value.isdigit():
                    return qs.none()
                qfilter &= Q(**{INT_EXACT[property_value]: int(search_value)})
            elif property_value in TEXT:
                qfilter &= Q(**{TEXT[property_value]: search_value})
            elif property_value in FK:
                id_lookup, name_lookup = FK[property_value]
                qfilter &= Q(**{id_lookup: int(search_value)}) if search_value.isdigit() else Q(**{name_lookup: search_value})
            elif property_value in M2M:
                id_lookup, name_lookup = M2M[property_value]
                needs_distinct = True
                qfilter &= Q(**{id_lookup: int(search_value)}) if search_value.isdigit() else Q(**{name_lookup: search_value})
            elif property_value in PERSON_PREFIX:
                needs_distinct = True
                qfilter &= _person(search_value, PERSON_PREFIX[property_value])
            elif property_value in {"vvo", "bvo"}:
                try:
                    val = Decimal(search_value)
                except InvalidOperation:
                    return qs.none()
                qfilter &= Q(**{("vastgoed__vvo" if property_value == "vvo" else "vastgoed__bvo"): val})
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
