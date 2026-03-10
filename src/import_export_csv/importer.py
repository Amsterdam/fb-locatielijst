import logging
from typing import Union

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from fblocatie.models import Adres, Locatie, Vastgoed
from import_export_csv.mappings import (
    ADRES_MAPPING,
    LOCATIE_MANY_TO_MANY_FIELDS,
    LOCATIE_MAPPING,
    LOCATIE_REFERENTIE_TABELLEN,
    VG_MAPPING,
    VG_REFERENTIE_TABELLEN,
)
from referentie_tabellen.models import (
    Persoon,
)

log = logging.getLogger(__name__)


class ImporterProcessCSV:
    def __init__(self):
        self.locatie_id = ""
        self.pandcode = ""
        self.errors = {}
        self.error_list = []
        self.adres_obj = None
        self.vastgoed_obj = None
        self.locatieteam_obj = None

    @staticmethod
    def set_empty_to_none(data: dict) -> dict:
        return {key: (None if value in ("", "x", "'-'", "?") else value) for key, value in data.items()}

    def process_adres(self, row: dict) -> Adres:
        self.error_list = []

        adres_mapping = ADRES_MAPPING
        data = {key: row.pop(value) for key, value in adres_mapping.items() if value in row}
        adres_data = self.set_empty_to_none(data)

        # data correction before dbstorage
        if "postcode" in adres_data and len(adres_data["postcode"]) > 6:
            adres_data["postcode"] = adres_data["postcode"].replace(" ", "")

        match_keys = ["postcode", "huisnummer", "huisletter", "huisnummertoevoeging"]
        match_adres = {key: adres_data[key] for key in match_keys if key in adres_data}

        update_fields = {key: value for key, value in adres_data.items() if key not in match_keys}

        try:
            obj, _ = Adres.objects.update_or_create(defaults=update_fields, **match_adres)
        except Exception as e:
            self.error_list.append(e)
            obj = None

        if self.error_list != []:
            self.errors["adres"] = self.error_list
            self.error_list = []
        # return obj
        self.adres_obj = obj

    @staticmethod
    def _get_persoon(naam: str) -> tuple[Union[Persoon, None], Union[tuple, None]]:
        error = None
        if naam is None:
            return None, error

        try:
            voornaam, achternaam = naam.strip().split(" ", 1)
            obj = Persoon.objects.get(voornaam=voornaam.strip(), achternaam=achternaam.strip())
        except (ValueError, Persoon.DoesNotExist) as e:
            error = (f"{naam}", e)
            obj = None
        return obj, error

    def get_referentietabellen_fields(self, referentie_tabellen: list, data: dict) -> dict:

        for field, model in referentie_tabellen:
            if data.get(field) is None:
                continue
            try:
                if model == Persoon:
                    obj, error = self._get_persoon(data[field])
                    if error is not None:
                        self.error_list.append(error)
                else:
                    obj = model.objects.get(name=data[field])
                data[field] = obj
            except ObjectDoesNotExist:
                self.error_list.append(f" '{data[field]}' is niet aanwezig in de {model} tabel")
                data[field] = None
        return data

    def process_vastgoed(self, row: dict) -> Vastgoed:
        self.error_list = []
        # model : row
        vg_mapping = VG_MAPPING
        referentie_tabellen = VG_REFERENTIE_TABELLEN

        data = {key: row.pop(value) for key, value in vg_mapping.items() if value in row}
        vg_data = self.set_empty_to_none(data)

        # data correction before dbstorage
        if "bezit" in vg_data and vg_data["bezit"] is None:
            vg_data["bezit"] = "ntb"  # nader te bepalen

        for k in ["vvo", "bvo"]:
            if vg_data.get(k) is not None:
                vg_data[k] = vg_data[k].replace(",", ".")

        # set adres onetoonefield
        vg_data["adres"] = self.adres_obj
        # get referentie fields
        vg_data = self.get_referentietabellen_fields(referentie_tabellen, vg_data)

        # update or create
        match_keys = ["adres"]
        match_vg = {key: vg_data[key] for key in match_keys if key in vg_data}

        update_fields = {key: value for key, value in vg_data.items() if key not in match_keys}

        try:
            obj, _ = Vastgoed.objects.update_or_create(defaults=update_fields, **match_vg)
        except Exception as e:
            self.error_list.append(e)
            obj = None

        if self.error_list != []:
            self.errors["vastgoed"] = self.error_list
            self.error_list = []
        # return obj
        self.vastgoed_obj = obj

    def _get_many_to_many(self, model, string: str, sep="|") -> list:
        objs = []
        if not string:
            return objs

        lijst = [s.strip() for s in string.split(sep)]
        for lst in lijst:
            try:
                if model == Persoon:
                    obj, error = self._get_persoon(lst)
                    if error is not None:
                        self.error_list.append(error)
                    else:
                        objs.append(obj.id)
                else:
                    obj = model.objects.get(name=lst)
                    objs.append(obj.id)
            except Exception as e:
                self.error_list = f"Error {lst} from {model}: {e}"

        return objs

    def main(self, row: dict):
        self.errors = {}

        with transaction.atomic():
            # print('start row: ', row)
            self.error_list = []
            # model : row
            locatie_mapping = LOCATIE_MAPPING
            many_to_many_fields = LOCATIE_MANY_TO_MANY_FIELDS
            referentie_tabellen = LOCATIE_REFERENTIE_TABELLEN

            data = {key: row.pop(value) for key, value in locatie_mapping.items() if value in row}
            loc_data = self.set_empty_to_none(data)

            # connect models in right order
            field_model_ids = [
                ("adres", self.process_adres),
                ("vastgoed", self.process_vastgoed),
            ]
            for field, func in field_model_ids:
                func(row)
                obj = getattr(self, field + "_obj")
                if obj is not None:
                    loc_data[field] = obj

            # get referentie fields location
            loc_data = self.get_referentietabellen_fields(referentie_tabellen, loc_data)

            # update or create locatie
            match_keys = ["pandcode", "afkorting"]
            match_loc = {key: loc_data[key] for key in match_keys if key in loc_data}

            update_fields = {
                key: value
                for key, value in loc_data.items()
                if key not in match_keys and key not in [a for a, b in many_to_many_fields]
            }

            try:
                self.pandcode = loc_data["pandcode"]
                self.locatie_id = loc_data["afkorting"]

                locatie, created = Locatie.objects.update_or_create(defaults=update_fields, **match_loc)

                for f, m in many_to_many_fields:
                    if f in loc_data:
                        lst_obj = self._get_many_to_many(string=loc_data[f], model=m)
                        if self.error_list != []:
                            continue
                        getattr(locatie, f).set(lst_obj)
            except Exception as e:
                self.error_list.append(f"locatie niet aangemaakt: {e}")

            if self.error_list != []:
                self.errors["locatie"] = self.error_list
                self.error_list = []

            # print(self.errors)
            # print('niet uitgelezen: ', row)
