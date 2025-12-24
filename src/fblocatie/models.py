from django.db import models
from django.db.models import Max

from referentie_tabellen.models import Directie, LocatieSoort, DienstverleningsKader, Voorziening, Persoon, LocatieBezit, MonumentStatus, GelieerdePartij


class TimeStampMixin(models.Model):
    created_at = models.DateTimeField(verbose_name="Aanmaakdatum", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Laatste wijziging", auto_now=True)

    class Meta:
        abstract = True


class LocatieTeam(TimeStampMixin):
    nummer = models.IntegerField(verbose_name="Locatieteam", blank=True, null=True)
    email = models.EmailField(verbose_name="Mailadres", blank=True, null=True)
    loc_manager = models.ForeignKey(Persoon, verbose_name="Locatiemanager", related_name="loc_manager", blank=True, null=True, on_delete=models.RESTRICT)
    loc_coordinator= models.ForeignKey(Persoon, verbose_name="Locatiecoordinator", related_name="loc_coordinator", blank=True, null=True, on_delete=models.RESTRICT)
    contact_directie =models.ForeignKey(Persoon, verbose_name="Contactpersoon vanuit directies", related_name="contact_directie", blank=True, null=True, on_delete=models.RESTRICT)
    tom = models.ForeignKey(Persoon, verbose_name="Technisch ojectmanager (TOM)", related_name="tom", blank=True, null=True, on_delete=models.RESTRICT)
    tsc = models.ForeignKey(Persoon, verbose_name="Technisch service coordinator (TSC)", related_name="tsc", blank=True, null=True,  on_delete=models.RESTRICT)
    beveiliging = models.ForeignKey(Persoon, verbose_name="Adviseur beveiliging", related_name="beveiliging", blank=True, null=True, on_delete=models.RESTRICT)
    veiligheid= models.ForeignKey(Persoon, verbose_name="Adviseur veiligheid", related_name="veiligheid", blank=True, null=True, on_delete=models.RESTRICT)
    perceel_installateur= models.ForeignKey(Persoon, verbose_name="E&W perceel installateur", related_name="perceel_installateur", blank=True, null=True, on_delete=models.RESTRICT)

    def __str__(self):
        return str(self.nummer)
    

# voor toekomstige BAG koppeling: in nummeraanduidingen zijn de koppelsleutels voor verblijfobjecten en openbareuruimtes te vinden
class Adres(models.Model):
    bag_id = models.CharField(verbose_name="BAG id", max_length=16, blank=True, null=True) 
    straat = models.CharField(max_length=80) ##kan opgehaald via /v1/bag/openbareruimtes 
    postcode = models.CharField(max_length=6) #kan opgehaald via /v1/bag/nummeraanduidingen/
    huisnummer = models.IntegerField() #kan opgehaald via /v1/bag/nummeraanduidingen/
    huisletter = models.CharField(max_length=41, blank=True, null=True) #kan opgehaald via /v1/bag/nummeraanduidingen/
    huisnummertoevoeging = models.CharField(max_length=4, blank=True, null=True) #kan opgehaald via /v1/bag/nummeraanduidingen/
    woonplaats = models.CharField(max_length=50) #kan opgehaald via /v1/bag/openbareruimtes
    lat = models.FloatField(verbose_name="Latitude", blank=True, null=True)
    long = models.FloatField(verbose_name="Longitude", blank=True, null=True)
    # geometry kan opgehaald via /v1/bag/verblijfsobjecten
    map_url = models.URLField(max_length=200)

    def save(self, *args, **kwargs):
        if self.lat is not None and self.long is not None:
            self.map_url = f"https://maps.google.com/?q={self.long},{self.lat}"

        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name_plural = "Adressen"


class Vastgoed(models.Model):
    adres = models.OneToOneField(Adres, on_delete=models.CASCADE, related_name='adres_extension')
    GV_key = models.CharField(verbose_name="GV(planon)", blank=True, null=True) 
    bezit=models.ForeignKey(LocatieBezit, verbose_name="Eigendom / Huur", on_delete=models.RESTRICT)
    bouwjaar= models.IntegerField(verbose_name="Bouwjaar", blank=True, null=True)
    vvo = models.DecimalField(verbose_name="Verhuurbaar vloeroppervlak (VVO)", max_digits=10, decimal_places=2, blank=True, null=True)
    bvo = models.DecimalField(verbose_name="Bruto vloeroppervlakte (BVO)", max_digits=10, decimal_places=2, blank=True, null=True)
    energielabel = models.CharField(verbose_name="Energielabel",max_length=5, blank=True, null=True)
    monumentstatus = models.ForeignKey(MonumentStatus, verbose_name="Monument status Amsterdam", on_delete=models.RESTRICT, blank=True, null=True)
    asset_manager =models.ForeignKey(Persoon, verbose_name="Assetmanager/contract vastgoed", related_name="asset_manager", blank=True, null=True, on_delete=models.RESTRICT)
    pl_gv=models.ForeignKey(Persoon, verbose_name="Projectleider Gemeentelijk Vastgoed", related_name="pl_gv", blank=True, null=True, on_delete=models.RESTRICT)

    class Meta:
        verbose_name_plural = "Vastgoed" 

# Auto generate a new pandcode based on the current highest in the database
def compute_pandcode() -> int:
    return (Locatie.objects.aggregate(Max("pandcode"))["pandcode__max"] or 0) + 1 

class Locatie(TimeStampMixin):
    """
    Base class for the location
    """
    afkorting = models.CharField(verbose_name="Afkorting", primary_key=True, max_length= 15) # uniek en identificeerbaar, gelijk aan pandcode in https://hoofdstad.sharepoint.com/sites/in-dga-pa
    pandcode = models.IntegerField(verbose_name="FB pandcode", default=compute_pandcode) #leidend voor externe leveranciers en datakoppelingen
    naam = models.CharField(verbose_name="Naam", unique=True, max_length=100)
    is_archived = models.BooleanField(verbose_name="Archief", default=False)
    beschrijving = models.TextField(verbose_name="Beschrijving", blank=True, default="")
    adres = models.ForeignKey(Adres, related_name="locatie_adres", on_delete=models.RESTRICT)
    vastgoed = models.ForeignKey(Vastgoed, related_name='locatie_vastgoed', on_delete=models.RESTRICT)
    locatie_soort = models.ForeignKey(LocatieSoort, on_delete=models.RESTRICT)
    dienstverleningskader = models.ForeignKey(DienstverleningsKader, on_delete=models.RESTRICT)
    # navragen: budgethouder directie zelfde opties als pand directies??
    budgethouder = models.ForeignKey(Directie, related_name="budgethouder", blank=True, null=True, on_delete=models.RESTRICT)
    routecode = models.CharField(max_length= 15, default="FB") #dit zijn opties in de huidige db?? gek - location_property_id=14???
    pand_directies = models.ManyToManyField(Directie, related_name="locatie_pand_directies")
    voorzieningen =  models.ManyToManyField(Voorziening)
    werkplekken = models.IntegerField(blank=True, null=True)
    locatieteam = models.ForeignKey(LocatieTeam, blank=True, null=True, on_delete=models.RESTRICT)
    gelieerd = models.ForeignKey(GelieerdePartij, blank=True, null=True, on_delete=models.RESTRICT)

    # externe koppelvelden
    pas_loc = models.CharField(verbose_name="1s1p locatie", blank=True, null=True) 
    anet_loc = models.CharField(verbose_name="A-net locatie", max_length=3, blank=True, null=True) 
    emobj = models.IntegerField(verbose_name="Energiemissie object", blank=True, null=True) 
    po = models.IntegerField(verbose_name= "P&O locatie code", blank=True, null=True) 

    def __str__(self):
        return f"{self.pandcode}, {self.naam}"

    def save(self, *args, **kwargs):
        if self.routecode is None:
            self.routecode = "FB" 
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["pandcode"]
