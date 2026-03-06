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
    "afkorting": "afkorting",
    "pandcode": "pandcode",
    "naam": "naam",
    "archief": "archief",
    "beschrijving": "beschrving",
    "bezoekadres_functie": "adres2_rol",
    "afstoten": "afstoten",
    "ambtenaar": "ambtenaar",
    "locatie_soort": "soort",
    "dvk_naam": "dvk_naam",
    "budget_dir": "budget_dir",
    "routecode": "routecode",
    "pand_directies": "vlekken",
    "voorzieningen": "voorz",
    "kantoorkast": "kantoorart",
    "werkplekken": "werkplek",
    "locatieteam": "lt",
    "loc_email": "lt_mail",
    "loc_manager": "lm",
    "loc_coordinator": "lc",
    "contact_dir": "contact",
    "tom": "tom",
    "tsc": "tsc",
    "beveiliging": "beveiligng",
    "veiligheid": "veiligheid",
    "perceel_installateur": "ew",
    "gelieerd": "gelieerd",
    "contracten": "contract",
    "notitie": "notitie",
    "pas_loc": "pas_loc",
    "pas_lc": "pas",
    "anet_loc": "anet_loc",
    "emobj": "emobj",
    "po": "po",
    "priva_gbs": "priva_gbs",
}


LOCATIE_MANY_TO_MANY_FIELDS = [
    ("pand_directies", Directie),
    ("voorzieningen", Voorziening),
    ("contracten", Contract),
]


LOCATIE_REFERENTIE_TABELLEN = [
    ("locatie_soort", LocatieSoort),
    ("dvk_naam", DienstverleningsKader),
    ("budget_dir", Directie),
    ("gelieerd", GelieerdePartij),
    ("loc_manager", Persoon),
    ("loc_coordinator", Persoon),
    ("contact_dir", Persoon),
    ("tom", Persoon),
    ("tsc", Persoon),
    ("beveiliging", Persoon),
    ("veiligheid", Persoon),
    ("perceel_installateur", OnderhoudsContract),
    ("pas_lc", Leverancier1s1p),
]
