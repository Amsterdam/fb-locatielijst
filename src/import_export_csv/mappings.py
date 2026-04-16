from referentie_tabellen.models import (
    Contract,
    DienstverleningsKader,
    Directie,
    GelieerdePartij,
    Leverancier1s1p,
    LocatieBezit,
    LocatieSoort,
    MonumentStatus,
    OnderhoudsContract,
    Persoon,
    ThemaPortefeuille,
    Voorziening,
)

# model : row
ADRES_MAPPING = {
    "pand_id": "bag_id",
    "vot_id": "vbo_id",
    "straat": "straat",
    "postcode": "postcode",
    "huisnummer": "huisnummer",
    "huisletter": "huisletter",
    "huisnummertoevoeging": "numtoeg",
    "woonplaats": "plaats",
    "rd_x": "rd_x",
    "rd_y": "rd_y",
}

EXPORT_ONLY_ADRES_MAPPING = {
    "lat": "latitude",
    "lon": "longitude",
    "map_url": "maps",
}


VG_MAPPING = {
    "GV_key": "gv",
    "gv_id": "gv_id",
    "bezit": "bezit",
    "bouwjaar": "bouwjaar",
    "vvo": "vvo",
    "bvo": "bvo",
    "energielabel": "energielbl",
    "monument_gem": "mon_gem",
    "monument_brkpb": "mon_brkpb",
    "themagv": "themagv",
    "asset_manager": "am_gv",
    "pl_gv": "plgv",
}


VG_REFERENTIE_TABELLEN = [
    ("bezit", LocatieBezit),
    ("monument_gem", MonumentStatus),
    ("monument_brkpb", MonumentStatus),
    ("themagv", ThemaPortefeuille),
    ("asset_manager", Persoon),
    ("pl_gv", Persoon),
]


LOCATIE_MAPPING = {
    "pandcode": "pandcode",
    "naam": "naam",
    "afkorting": "afkorting",
    "beschrijving": "beschrving",
    "archief": "archief",
    "afstoten": "afstoten",
    "ambtenaar": "ambtenaar",
    "locatie_soort": "soort",
    "werkplekken": "werkplek",
    "gelieerd": "gelieerd",
    "locatieteam": "lt",
    "loc_email": "lt_mail",
    "dvk_naam": "dvk_naam",
    "budget_dir": "budget_dir",
    "routecode": "routecode",
    "pand_directies": "vlekken",
    "bezoekadres_functie": "adres2_rol",
    "loc_manager": "lm",
    "loc_coordinator": "lc",
    "contact_dir": "contact",
    "tom": "tom",
    "tsc": "tsc",
    "beveiliging": "beveiligng",
    "veiligheid": "veiligheid",
    "perceel_installateur": "ew",
    "voorzieningen": "voorz",
    "kantoorkast": "kantoorart",
    "contracten": "contract",
    "notitie": "notitie",
    "emobj": "emobj",
    "priva_gbs": "priva_gbs",
    "po": "po",
    "pas_lc": "pas",
    "pas_loc": "pas_loc",
    "anet_loc": "anet_loc",
}


LOCATIE_MANY_TO_MANY_FIELDS = [
    ("pand_directies", Directie),
    ("voorzieningen", Voorziening),
    ("contracten", Contract),
    ("loc_manager", Persoon),
    ("loc_coordinator", Persoon),
    ("contact_dir", Persoon),
    ("tom", Persoon),
    ("tsc", Persoon),
    ("beveiliging", Persoon),
    ("veiligheid", Persoon),
]


LOCATIE_REFERENTIE_TABELLEN = [
    ("locatie_soort", LocatieSoort),
    ("dvk_naam", DienstverleningsKader),
    ("budget_dir", Directie),
    ("gelieerd", GelieerdePartij),
    ("perceel_installateur", OnderhoudsContract),
    ("pas_lc", Leverancier1s1p),
]
