from __future__ import annotations

from typing import Any

from fblocatie.models import Locatie


def _display_value(value: Any):
    if value is None:
        return None

    if isinstance(value, bool):
        return "Ja" if value else "Nee"

    # Handle many-to-many values
    if hasattr(value, "all") and callable(value.all):
        items = [str(item) for item in value.all()]
        return items or None

    return str(value) if str(value).strip() else None


def _row(label: str, value: Any, *, is_url: bool = False) -> dict[str, Any]:
    return {
        "label": label,
        "value": _display_value(value),
        "is_url": is_url,
    }


def get_locatie_detail_groups(locatie: Locatie) -> list[dict[str, Any]]:
    adres = getattr(locatie, "adres", None)
    bezoekadres = getattr(locatie, "bezoekadres", None)
    vastgoed = getattr(locatie, "vastgoed", None)

    return [
        {
            "title": None,
            "rows": [
                _row("Pandcode", locatie.pandcode),
                _row("Naam", locatie.naam),
            ],
        },
        {
            "title": "Algemeen",
            "rows": [
                _row("Afkorting", locatie.afkorting),
                _row("Beschrijving", locatie.beschrijving),
                _row("Actief", not locatie.archief),
                _row("Afstoten", locatie.afstoten),
                _row("Gemeentelijke huisvesting", locatie.ambtenaar),
                _row("Soort locatie", locatie.locatie_soort),
                _row("Aantal werkplekken", locatie.werkplekken),
                _row("Gelieerde partij", locatie.gelieerd),
                _row("Locatieteam", locatie.locatieteam),
                _row("Mailadres locatieteam", locatie.loc_email),
                _row("Categorie dienstverleningskader", locatie.dvk_naam),
                _row("Budget verantwoordelijke directie", locatie.budget_dir),
                _row("Routecode indien geen budget FB", locatie.routecode),
                _row("Directies in het pand", locatie.pand_directies),
                _row("Voorzieningen", locatie.voorzieningen),
                _row("Contracten op deze locatie", locatie.contracten),
                _row("Kantoorartikelkast uitgebreid assortiment", locatie.kantoorkast),
            ],
        },
        {
            "title": "Adresgegevens",
            "rows": [
                _row("Adres", adres),
                _row("Straat", getattr(adres, "straat", None) if adres else None),
                _row("Postcode", getattr(adres, "postcode", None) if adres else None),
                _row("Huisnummer", getattr(adres, "huisnummer", None) if adres else None),
                _row("Huisletter", getattr(adres, "huisletter", None) if adres else None),
                _row("Nummer toevoeging", getattr(adres, "huisnummertoevoeging", None) if adres else None),
                _row("Plaats", getattr(adres, "woonplaats", None) if adres else None),
                _row("Kaart (adres)", getattr(adres, "map_url", None) if adres else None, is_url=True),
                _row("Bezoekadres", bezoekadres),
            ],
        },
        {
            "title": "Contacten",
            "rows": [
                _row("Locatiemanager", locatie.loc_manager),
                _row("Locatiecoördinator", locatie.loc_coordinator),
                _row("Contactpersoon vanuit directies", locatie.contact_dir),
                _row("Technisch objectmanager (TOM)", locatie.tom),
                _row("Technisch service coördinator (TSC)", locatie.tsc),
                _row("Adviseur beveiliging", locatie.beveiliging),
                _row("Adviseur veiligheid", locatie.veiligheid),
                _row(
                    "Assetmanager/contact vastgoed",
                    getattr(vastgoed, "asset_manager", None) if vastgoed else None,
                ),
                _row(
                    "Projectleider Gemeentelijk vastgoed",
                    getattr(vastgoed, "pl_gv", None) if vastgoed else None,
                ),
                _row("E&W perceel installateur", locatie.perceel_installateur),
            ],
        },
        {
            "title": "Externe koppelingen",
            "rows": [
                _row("BAG id (pand)", getattr(adres, "pand_id", None) if adres else None),
                _row("BAG id (verblijfsobject)", getattr(adres, "vot_id", None) if adres else None),
                _row("1s1p locatie", locatie.pas_loc),
                _row("Leverancier van 1s1p", locatie.pas_lc),
                _row("A-net afkorting locatie", locatie.anet_loc),
                _row("Energiemissie object", locatie.emobj),
                _row("GV(planon)", getattr(vastgoed, "GV_key", None) if vastgoed else None),
                _row("BRES ID", getattr(vastgoed, "gv_id", None) if vastgoed else None),
                _row("P&O locatie code", locatie.po),
                _row("Locatie Priva GBS", locatie.priva_gbs),
            ],
        },
        {
            "title": "GV",
            "rows": [
                _row("Eigendom / Huur", getattr(vastgoed, "bezit", None) if vastgoed else None),
                _row("Bouwjaar", getattr(vastgoed, "bouwjaar", None) if vastgoed else None),
                _row("Verhuurbaar vloeroppervlak (VVO)", getattr(vastgoed, "vvo", None) if vastgoed else None),
                _row("Bruto vloeroppervlakte (BVO)", getattr(vastgoed, "bvo", None) if vastgoed else None),
                _row("Energielabel", getattr(vastgoed, "energielabel", None) if vastgoed else None),
                _row(
                    "Monument status Amsterdam",
                    getattr(vastgoed, "monument_gem", None) if vastgoed else None,
                ),
                _row(
                    "Monument status landelijk",
                    getattr(vastgoed, "monument_brkpb", None) if vastgoed else None,
                ),
                _row(
                    "Themaportefeuille GV",
                    getattr(vastgoed, "themagv", None) if vastgoed else None,
                ),
            ],
        },
        {
            "title": "Overig",
            "rows": [
                _row("Notitie", locatie.notitie),
            ],
        },
    ]
