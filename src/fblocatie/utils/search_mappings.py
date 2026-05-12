TEXT_FIELD_LOOKUPS: dict[str, str] = {
	"naam": "naam__icontains",
	"afkorting": "afkorting__icontains",
	"beschrving": "beschrijving__icontains",
	"lt_mail": "loc_email__icontains",
	"routecode": "routecode__icontains",
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

DEFAULT_INT_LOOKUPS: dict[str, str] = {
    "pandcode": "pandcode",
}

DEFAULT_TEXT_LOOKUPS: tuple[str, ...] = tuple(sorted(set(TEXT_FIELD_LOOKUPS.values())))

FOREIGN_KEY_LOOKUPS: dict[str, tuple[str, str]] = {
	"soort": ("locatie_soort_id", "locatie_soort__name__icontains"),
	"dvk_naam": ("dvk_naam_id", "dvk_naam__name__icontains"),
	"budget_dir": ("budget_dir_id", "budget_dir__name__icontains"),
	"themagv": ("vastgoed__themagv_id", "vastgoed__themagv__name__icontains"),
	"ew": ("perceel_installateur_id", "perceel_installateur__name__icontains"),
	"bezit": ("vastgoed__bezit_id", "vastgoed__bezit__name__icontains"),
	"mon_brkpb": ("vastgoed__monument_brkpb_id", "vastgoed__monument_brkpb__name__icontains"),
}


MANY_TO_MANY_LOOKUPS: dict[str, tuple[str, str]] = {
	"vlekken": ("pand_directies__id", "pand_directies__name__icontains"),
	"voorz": ("voorzieningen__id", "voorzieningen__name__icontains"),
	"contract": ("contracten__id", "contracten__name__icontains"),
}


INT_FIELD_LOOKUPS: dict[str, str] = {
    "pandcode": "pandcode",
	"werkplek": "werkplekken",
	"lt": "locatieteam",
	"huisnummer": "adres__huisnummer",
	"bouwjaar": "vastgoed__bouwjaar",
}


PERSON_LOOKUP_PREFIXES: dict[str, str] = {
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
