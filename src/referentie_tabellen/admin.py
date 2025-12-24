from django.contrib import admin
from referentie_tabellen.models import DienstverleningsKader, Directie, LocatieBezit, LocatieSoort, Persoon, GelieerdePartij, MonumentStatus, Voorziening

@admin.register(DienstverleningsKader)
class DienstverleningsKaderAdmin(admin.ModelAdmin):
    list_display = ("id", "name",)
    ordering = ("name",)


@admin.register(Directie)
class DirectieAdmin(admin.ModelAdmin):
    list_display = ("id", "name",)
    ordering = ("name",)


@admin.register(LocatieBezit)
class LocatieBezitAdmin(admin.ModelAdmin):
    list_display = ("id", "name",)
    ordering = ("name",)


@admin.register(LocatieSoort)
class LocatieSoortAdmin(admin.ModelAdmin):
    list_display = ("id", "name",)
    ordering = ("name",)


@admin.register(Persoon)
class PersoonAdmin(admin.ModelAdmin):
    list_display = ("id", "voornaam", "achternaam")
    ordering = ("achternaam",)


@admin.register(GelieerdePartij)
class GelieerdePartijAdmin(admin.ModelAdmin):
    list_display = ("id", "name",)
    ordering = ("name",)                


@admin.register(MonumentStatus)
class MonumentStatusAdmin(admin.ModelAdmin):
    list_display = ("id", "name",)
    ordering = ("name",)  


@admin.register(Voorziening)
class VoorzieningAdmin(admin.ModelAdmin):
    list_display = ("id", "name",)
    ordering = ("name",)          