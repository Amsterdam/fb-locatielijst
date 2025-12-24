from django.apps import apps
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction

from fblocatie.models import Adres, Vastgoed, LocatieTeam, Locatie
from referentie_tabellen.models import LocatieBezit, MonumentStatus, Persoon, LocatieSoort, GelieerdePartij, DienstverleningsKader, Directie, Voorziening

from typing import Union

class ImporterProcessCSV:
    
    def __init__(self):
        self.locatie_id = ''
        self.pandcode = ''
        self.errors = {}
        self.error_list = []
        self.adres_obj = None
        self.vastgoed_obj = None
        self.locatieteam_obj = None
        
    @staticmethod
    def set_empty_to_none(data: dict) -> dict:
        return {key: (None if value in ('','x', '\'-\'') else value) for key, value in data.items()}


    def process_adres(self, row: dict)-> Adres:
        self.error_list = []
        # model : row
        adres_mapping = {
            'bag_id': 'bag_id',
            'straat': 'straat', 
            'postcode': 'postcode', 
            'huisnummer': 'huisnummer', 
            'huisletter': 'huisletter', 
            'huisnummertoevoeging': 'numtoeg', 
            'woonplaats': 'plaats', 
            'long': 'longitude', 
            'lat': 'latitude', 
        }
        data = {key: row.get(value) for key, value in adres_mapping.items() if value in row}
        adres_data = self.set_empty_to_none(data)

        match_keys = ['postcode', 'huisnummer', 'huisletter', 'huisnummertoevoeging']
        match_adres = {key: adres_data[key] for key in match_keys if key in adres_data}
        
        update_fields = {key: value for key, value in adres_data.items() if key not in match_keys}

        try:
            obj, _ = Adres.objects.update_or_create(defaults = update_fields, **match_adres)
        except Exception as e:
            print(e)
            self.error_list.append(e)
            obj = None   

        if self.error_list !=[]:
            self.errors['adres'] = self.error_list
            self.error_list=[]            
        # return obj
        self.adres_obj=obj


    @staticmethod
    def _get_persoon(naam:str)-> Union[Persoon, str]:
        # TODO: er komen meerdere personen soms via '/' voor -> multi?
        error = ''
        if naam == None:
            return None, error
        
        try:
            voornm, achternm = naam.split(' ',1)
            obj = Persoon.objects.get(voornaam= voornm.strip(), achternaam=achternm.strip())
        except Exception as e:
            error = (f'{naam}', e)
            obj = None
        return obj, error


    def get_referentietabellen_fields(self, referentie_tabellen: list, data: dict ) -> list:

        for field, model in referentie_tabellen:
            if data[field] is None:
                continue
            try:
                if model == Persoon:
                    obj, e = self._get_persoon(data[field])
                    if e != '':
                        self.error_list.append(e)
                else:    
                    obj = model.objects.get(name = data[field])
                data[field] = obj
            except ObjectDoesNotExist:
                self.error_list.append(f" '{data[field]}' is niet aanwezig in de {model} tabel")
                data[field]=None


    def process_vastgoed(self,row: dict)-> Vastgoed:
        self.error_list = []
        # model : row
        vg_mapping = {
            'GV_key': 'gv',
            'bezit': 'bezit', 
            'bouwjaar': 'bouwjaar', 
            'vvo': 'vvo', 
            'bvo': 'bvo', 
            'energielabel': 'energielbl', 
            'monumentstatus': 'mon_gem', 
            'asset_manager': 'am_gv', 
            'pl_gv': 'plgv', 
        }
        referentie_tabellen = [('bezit', LocatieBezit), ('monumentstatus', MonumentStatus), ('asset_manager', Persoon), ('pl_gv', Persoon)]

        data = {key: row.get(value) for key, value in vg_mapping.items() if value in row}
        vg_data = self.set_empty_to_none(data)

        # set adres onetoonefield
        vg_data['adres'] = self.adres_obj
        # get referentie fields
        self.get_referentietabellen_fields(referentie_tabellen, vg_data)
    
        # update or create
        match_keys = ['adres']
        match_vg = {key: vg_data[key] for key in match_keys if key in vg_data}
        
        update_fields = {key: value for key, value in vg_data.items() if key not in match_keys}
        
        try:
            obj, _ = Vastgoed.objects.update_or_create(defaults = update_fields, **match_vg)
        except Exception as e:
            self.error_list.append(e)
            obj = None

        if self.error_list !=[]:
            self.errors['vastgoed'] = self.error_list 
            self.error_list=[]              
        # return obj
        self.vastgoed_obj=obj


    def process_locatieteam(self, row: dict) -> Locatie:
        self.error_list = []
        # model : row
        locatieteam_mapping = {
            'nummer': 'lt', 
            'email': 'lt_mail',
            'loc_manager': 'lm', 
            'loc_coordinator': 'lc', 
            'contact_directie': 'contact', 
            'tom': 'tom', 
            'tsc': 'tsc', 
            'beveiliging': 'beveiligng', 
            'veiligheid': 'veiligheid', 
            'perceel_installateur': 'ew', 
        }
        referentie_tabellen = [('loc_manager', Persoon), ('loc_coordinator', Persoon), ('contact_directie', Persoon), ('tom', Persoon), 
                            ('tsc', Persoon), ('beveiliging', Persoon), ('veiligheid', Persoon), ('perceel_installateur', Persoon)]

        data = {key: row.get(value) for key, value in locatieteam_mapping.items() if value in row}
        lt_data = self.set_empty_to_none(data)

        # get referentie fields
        self.get_referentietabellen_fields(referentie_tabellen, lt_data)

        match_keys = ['nummer', 'lt_mail']
        match_adres = {key: lt_data[key] for key in match_keys if key in lt_data}
        
        update_fields = {key: value for key, value in lt_data.items() if key not in match_keys}

        try:
            obj, _ = LocatieTeam.objects.update_or_create(defaults = update_fields, **match_adres)
        except Exception as e:
            self.error_list.append(e)
            obj = None

        if self.error_list !=[]:
            self.errors['locatieteam'] = self.error_list
            self.error_list=[]
        # return obj                 
        self.locatieteam_obj=obj
        

    def _get_many_to_many(self, model, string: str, sep='|')-> list:
        objs = []
        if not string:
            return objs
        
        lijst = string.split(sep)
        for l in lijst:
            try:
                obj = model.objects.get(name = l)
                objs.append(obj.id)
            except Exception as e:
                self.error_list = f'Error {l} from {model}: {e}'

        return objs


    def main(self, row: dict):
        self.errors = {}

        with transaction.atomic():
            
            # model : row
            locatie_mapping = {
                'afkorting': 'afkorting',
                'pandcode': 'pandcode',
                'naam': 'naam',
                'is_archived': 'archief',
                'beschrijving': 'beschrving',
                'locatie_soort': 'soort',
                'dienstverleningskader': 'dvk_naam',
                'budgethouder': 'budget_dir',
                'routecode': 'routecode',
                'pand_directies': 'vlekken',
                'voorzieningen': 'voorz',
                'werkplekken': 'werkplek',
                'gelieerd': 'gelieerd',
                'pas_loc': 'pas_loc',
                'anet_loc': 'anet_loc',
                'emobj': 'emobj',
                'po': 'po',
            }
            many_to_many_fields = [('pand_directies', Directie), ('voorzieningen', Voorziening)]
            referentie_tabellen = [('locatie_soort', LocatieSoort), ('dienstverleningskader', DienstverleningsKader), ('budgethouder', Directie), ('gelieerd', GelieerdePartij)]

            data = {key: row.get(value) for key, value in locatie_mapping.items() if value in row}
            loc_data = self.set_empty_to_none(data)

            self.locatie_id = loc_data['afkorting']
            self.pandcode = loc_data['pandcode']

            # get referentie fields
            self.get_referentietabellen_fields(referentie_tabellen, loc_data)

            # connect models in right order
            field_model_ids = [('adres', self.process_adres), 
                               ('vastgoed', self.process_vastgoed), 
                               ('locatieteam', self.process_locatieteam)]
            for field, func in field_model_ids:
                func(row)
                loc_data[field] = getattr(self, field + '_obj')

            print(self.adres_obj)
            print('loc ',loc_data['adres'])
            print(self.locatie_id)

            # update or create locatie
            match_keys = ['pandcode', 'afkorting']
            match_loc = {key: loc_data[key] for key in match_keys if key in loc_data}
            
            update_fields = {key: value for key, value in loc_data.items() if key not in match_keys and key not in  [a for a, b in many_to_many_fields]}

            try:
                locatie, created = Locatie.objects.update_or_create(defaults = update_fields, **match_loc)
            except Exception as e:
                self.error_list.append(e)

            try: 
                locatie      
                for f, m in many_to_many_fields:
                    lst_obj = self._get_many_to_many(string=loc_data[f], model=m)
                    if self.error_list != []:
                        continue    
                    getattr(locatie, f).set(lst_obj)
            except Exception as e:
                self.error_list.append(f'locatie niet aangemaakt: {e}')
            
            if self.error_list !=[]:
                self.errors['locatie'] = self.error_list

            print(self.errors)
            print(row)

            