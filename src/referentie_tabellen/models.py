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
        verbose_name_plural = "Locatiesoorten"


class GelieerdePartij(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = "GelieerdePartijen"


class DienstverleningsKader(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    

class LocatieBezit(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Locatiebezit"


class MonumentStatus(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Monumentstatussen"


class Voorziening(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Voorzieningen"


class Persoon(models.Model):
    voornaam = models.CharField(max_length= 50)
    achternaam = models.CharField(max_length = 50)

    def __str__(self):
        return f"{self.voornaam} {self.achternaam}"

    class Meta:
        verbose_name_plural = "Personen"
        constraints = [
                models.UniqueConstraint(fields=['voornaam', 'achternaam'], name='unique_voornaam_achternaam')
            ]