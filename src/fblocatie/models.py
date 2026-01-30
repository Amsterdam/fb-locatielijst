from django.db import models
from django.db.models import Max
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.utils import timezone


from referentie_tabellen.models import Directie, LocatieSoort, DienstverleningsKader, Voorziening, Persoon, LocatieBezit, MonumentStatus, GelieerdePartij, Contract, ThemaPortefeuille, Leverancier1s1p


class TimeStampMixin(models.Model):
    created_at = models.DateTimeField(verbose_name="Aanmaakdatum", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Laatste wijziging", auto_now=True)

    class Meta:
        abstract = True


class LocatieTeam(TimeStampMixin):
    nummer = models.IntegerField(verbose_name="Locatieteam", blank=True, null=True)
    email = models.EmailField(verbose_name="Mailadres", blank=True, null=True)
    loc_manager = models.ForeignKey(Persoon, verbose_name="Locatiemanager", related_name="loc_manager", blank=True, null=True, on_delete=models.RESTRICT)

    def __str__(self):
        return f"Team {str(self.nummer)} '{self.email}'"
    

def calc_lat_lon_from_geometry(rd_x, rd_y) -> dict:
    """Calculate Point latitude and longitude (srid=4326; WGS coordinates) from given geometry in srid=28992 (RD-coordinates)"""
    point_rd = Point(rd_x, rd_y, srid=28992)
    point_wgs84 = point_rd.transform(4326, clone=True)
    return {"lat": point_wgs84.y, "lon": point_wgs84.x}

# voor toekomstige BAG koppeling: in nummeraanduidingen zijn de koppelsleutels voor verblijfobjecten en openbareuruimtes te vinden
class Adres(models.Model):
    pand_id = models.CharField(verbose_name="Pand identificatie", max_length=16, blank=True, null=True)
    vot_id = models.CharField(verbose_name="Verblijfsobject identificatie", max_length=16, blank=True, null=True)
    straat = models.CharField(max_length=80) ##kan opgehaald via /v1/bag/openbareruimtes 
    postcode = models.CharField(max_length=6) #kan opgehaald via /v1/bag/nummeraanduidingen/
    huisnummer = models.IntegerField() #kan opgehaald via /v1/bag/nummeraanduidingen/
    huisletter = models.CharField(max_length=41, blank=True, null=True) #kan opgehaald via /v1/bag/nummeraanduidingen/
    huisnummertoevoeging = models.CharField(max_length=4, blank=True, null=True) #kan opgehaald via /v1/bag/nummeraanduidingen/
    woonplaats = models.CharField(max_length=50) #kan opgehaald via /v1/bag/openbareruimtes
    rd_x = models.FloatField(verbose_name="RD_x", blank=True, null=True)
    rd_y = models.FloatField(verbose_name="RD_y", blank=True, null=True)
    lat = models.FloatField(verbose_name="Latitude", blank=True, null=True)
    lon = models.FloatField(verbose_name="Longitude", blank=True, null=True)
    # geometry kan opgehaald via /v1/bag/verblijfsobjecten
    map_url = models.URLField(max_length=200)

    def clean(self):
        super().clean()
        # Validate form input identification
        if self.pand_id and self.pand_id[4:6]!= "10": #positie 5-6: 10 = een pand 
            raise ValidationError(f"{self.pand_id} is geen geldige pandidentificatie.")
        if self.vot_id and self.vot_id[4:6]!= "01": #positie 5-6: 01 = een verblijfsobject
            raise ValidationError(f"{self.vot_id} is geen geldige verblijfsobjectidentificatie.")


    def save(self, *args, **kwargs):
        if None not in (self.rd_x, self.rd_y):
            rd_x = float(self.rd_x)
            rd_y = float(self.rd_y)
            pnt = calc_lat_lon_from_geometry(rd_x, rd_y)
            self.lat = round(pnt["lat"], 6)
            self.lon = round(pnt["lon"], 6)   
            self.map_url = f"https://data.amsterdam.nl/data/geozoek?center={self.lat}%2C{self.lon}&locatie={self.lat}%2C{self.lon}+&zoom=10"

        super().save(*args, **kwargs)

    def __str__(self):
        adres_str = f"{self.straat} {str(self.huisnummer)}"
        adres_str += f"{self.huisletter}" if self.huisletter else ""
        adres_str += f"{self.huisnummertoevoeging}" if self.huisnummertoevoeging else ""
        return adres_str
        
    class Meta:
        verbose_name_plural = "Adressen"

# voor toekomstige koppeling met Gemeentelijk Vastgoed
class Vastgoed(models.Model):
    adres = models.OneToOneField(Adres, on_delete=models.CASCADE, related_name='adres_extension')
    GV_key = models.CharField(verbose_name="GV(planon)", blank=True, null=True) 
    gv_id =  models.CharField(verbose_name="BRES ID", blank=True, null=True) 
    bezit=models.ForeignKey(LocatieBezit, verbose_name="Eigendom / Huur", on_delete=models.RESTRICT)
    bouwjaar= models.IntegerField(verbose_name="Bouwjaar", blank=True, null=True)
    vvo = models.DecimalField(verbose_name="Verhuurbaar vloeroppervlak (VVO)", max_digits=10, decimal_places=2, blank=True, null=True)
    bvo = models.DecimalField(verbose_name="Bruto vloeroppervlakte (BVO)", max_digits=10, decimal_places=2, blank=True, null=True)
    energielabel = models.CharField(verbose_name="Energielabel",max_length=5, blank=True, null=True)
    monument_gem = models.ForeignKey(MonumentStatus, verbose_name="Monument status Amsterdam", related_name="monument_gem", on_delete=models.RESTRICT, blank=True, null=True)
    monument_brkpb = models.ForeignKey(MonumentStatus, verbose_name="Monument status landelijk", related_name="monument_land", on_delete=models.RESTRICT, blank=True, null=True)
    themagv = models.ForeignKey(ThemaPortefeuille, verbose_name="Themaportefeuille", on_delete=models.RESTRICT, blank=True, null=True)
    asset_manager =models.ForeignKey(Persoon, verbose_name="Assetmanager/contract vastgoed", related_name="asset_manager", blank=True, null=True, on_delete=models.RESTRICT)
    pl_gv=models.ForeignKey(Persoon, verbose_name="Projectleider Gemeentelijk Vastgoed", related_name="pl_gv", blank=True, null=True, on_delete=models.RESTRICT)

    def __str__(self):
        #return f"{self.GV_key} {self.bezit}"
        return f"Vastgoed {self.adres}"
    
    class Meta:
        verbose_name_plural = "Vastgoed" 

# Auto generate a new pandcode based on the current highest in the database
def compute_pandcode() -> int:
    return (Locatie.objects.aggregate(Max("pandcode"))["pandcode__max"] or 0) + 1 

class Locatie(TimeStampMixin):
    """
    Base class for the location
    """

    pandcode = models.IntegerField(verbose_name="FB pandcode", primary_key=True, default=compute_pandcode) #leidend voor externe leveranciers en datakoppelingen
    afkorting = models.CharField(verbose_name="Afkorting", max_length= 15) # uniek en identificeerbaar, gelijk aan pandcode in https://hoofdstad.sharepoint.com/sites/in-dga-pa
    naam = models.CharField(verbose_name="Naam", unique=True, max_length=100)
    archief = models.BooleanField(verbose_name="Archief", default=False)
    archief_datum = models.DateTimeField(blank=True, null=True)
    beschrijving = models.TextField(verbose_name="Beschrijving", blank=True, null=True)
    adres = models.ForeignKey(Adres, related_name="locatie_adres", on_delete=models.RESTRICT)
    bezoekadres = models.ForeignKey(Adres, related_name="bezoek_adres", on_delete=models.RESTRICT, blank=True, null=True)
    bezoekadres_functie = models.CharField(verbose_name="Functie afwijkend adres", max_length=100, blank=True, null=True)
    vastgoed = models.ForeignKey(Vastgoed, related_name='locatie_vastgoed', on_delete=models.RESTRICT, blank=True, null=True)
    locatie_soort = models.ForeignKey(LocatieSoort, on_delete=models.RESTRICT)

    afstoten = models.DateField(blank=True, null=True)
    ambtenaar = models.BooleanField(verbose_name="Primair huisvesting ambtenaren", default=False)

    dvk_naam = models.ForeignKey(DienstverleningsKader, on_delete=models.RESTRICT)
    dvk_nr = models.IntegerField(blank=True, null=True)
    # navragen: budgethouder directie zelfde opties als pand directies??
    budget_dir = models.ForeignKey(Directie, related_name="budgethouder", blank=True, null=True, on_delete=models.RESTRICT)
    routecode = models.CharField(max_length= 15, default="FB") #dit zijn opties in de huidige db?? gek - location_property_id=14???
    pand_directies = models.ManyToManyField(Directie, related_name="locatie_pand_directies")
    voorzieningen =  models.ManyToManyField(Voorziening, blank=True)
    contracten = models.ManyToManyField(Contract, blank=True)
    werkplekken = models.IntegerField(blank=True, null=True)
    locatieteam = models.ForeignKey(LocatieTeam, blank=True, null=True, on_delete=models.RESTRICT)

    # contactpersonen
    loc_coordinator= models.ForeignKey(Persoon, verbose_name="Locatiecoordinator", related_name="loc_coordinator", blank=True, null=True, on_delete=models.RESTRICT)
    contact_dir =models.ForeignKey(Persoon, verbose_name="Contactpersoon vanuit directies", related_name="contact_directie", blank=True, null=True, on_delete=models.RESTRICT)
    tom = models.ForeignKey(Persoon, verbose_name="Technisch ojectmanager (TOM)", related_name="tom", blank=True, null=True, on_delete=models.RESTRICT)
    tsc = models.ForeignKey(Persoon, verbose_name="Technisch service coordinator (TSC)", related_name="tsc", blank=True, null=True,  on_delete=models.RESTRICT)
    beveiliging = models.ForeignKey(Persoon, verbose_name="Adviseur beveiliging", related_name="beveiliging", blank=True, null=True, on_delete=models.RESTRICT)
    veiligheid= models.ForeignKey(Persoon, verbose_name="Adviseur veiligheid", related_name="veiligheid", blank=True, null=True, on_delete=models.RESTRICT)
    perceel_installateur= models.ForeignKey(Persoon, verbose_name="E&W perceel installateur", related_name="perceel_installateur", blank=True, null=True, on_delete=models.RESTRICT)

    gelieerd = models.ForeignKey(GelieerdePartij, blank=True, null=True, on_delete=models.RESTRICT)
    kantoorkast = models.CharField(verbose_name= "Kantoorartikelkast", max_length=50, blank=True, null=True)
    notitie = models.TextField(blank=True, null=True)

    # externe koppelvelden
    pas_loc = models.CharField(verbose_name="1s1p locatie", blank=True, null=True)
    pas_lc = models.ForeignKey(Leverancier1s1p, verbose_name="leverancier van 1s1p", blank=True, null=True, on_delete=models.RESTRICT)
    anet_loc = models.CharField(verbose_name="A-net afkorting locatie", max_length=3, blank=True, null=True) 
    emobj = models.IntegerField(verbose_name="Energiemissie object", blank=True, null=True) 
    po = models.IntegerField(verbose_name= "P&O locatie code", blank=True, null=True)
    priva_gbs = models.CharField(verbose_name= "Locatie Priva GBS", max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.pandcode}, {self.naam}"

    def clean(self):
        super().clean()
        # Validate form input that the selected vastgoed matches the selected adres
        if self.vastgoed and self.vastgoed.adres != self.adres:
            raise ValidationError("Het geselecteerde vastgoed behoort niet tot het geselecteerde adres.")

    def save(self, *args, **kwargs):
        # set default routecode
        if self.routecode is None:
            self.routecode = "FB" 

        # Automatic set the vastgoed based on the adres else None
        if self.adres:
            try:
                self.vastgoed = Vastgoed.objects.get(adres=self.adres)
            except Vastgoed.DoesNotExist:
                self.vastgoed = None

        # set archief datum if not set yet
        if self.archief == 'True' and self.archief_datum == None:
            self.archief_datum = timezone.now()

        # change field ambtenaar if Ja/Nee ipv True/False
        match self.ambtenaar:
            case 'ja'|'Ja':
                self.ambtenaar = 'True'
            case 'nee'|'Nee':
                self.ambtenaar = 'False'


        super().save(*args, **kwargs)

    class Meta:
        ordering = ["pandcode"]
