from django.db import models


class Directie(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class LocatieSoort(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Locatie soorten"


class GelieerdePartij(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Gelieerde partijen"


class DienstverleningsKader(models.Model):
    name = models.CharField(max_length=100, unique=True)
    dvk_nr = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name


class LocatieBezit(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Locatie bezit"


class MonumentStatus(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Monument statussen"


class Voorziening(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Voorzieningen"


class Contract(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Contracten"


class Persoon(models.Model):
    voornaam = models.CharField(max_length=50)
    achternaam = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.voornaam} {self.achternaam}"

    class Meta:
        verbose_name_plural = "Personen"
        constraints = [models.UniqueConstraint(fields=["voornaam", "achternaam"], name="unique_voornaam_achternaam")]


class ThemaPortefeuille(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
        

class Leverancier1s1p(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Leverancier 1s1p"


class OnderhoudsContract(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Onderhouds contracten"