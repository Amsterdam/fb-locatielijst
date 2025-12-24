from django.contrib import admin
from fblocatie.models import Locatie, LocatieTeam, Adres, Vastgoed


@admin.register(Locatie)
class LocatieAdmin(admin.ModelAdmin):
    change_list_template = "fblocatie/locatie_changelist.html"

    list_display = ("afkorting", "pandcode", "naam", "locatieteam", "werkplekken", "vastgoed__bezit")
    ordering = ("pandcode",)
    search_fields = ("afkorting", "naam", "pandcode")
    search_help_text = "zoek op afkorting, naam of pandcode"

    list_filter = ("is_archived", "vastgoed__bezit", "locatieteam")

@admin.register(LocatieTeam)
class LocatieTeamAdmin(admin.ModelAdmin):
    list_display = ("nummer","id")
    ordering = ("id",)


@admin.register(Adres)
class AdresAdmin(admin.ModelAdmin):
    list_display = ("bag_id","id")
    ordering = ("id",)    


@admin.register(Vastgoed)
class VastgoedAdmin(admin.ModelAdmin):
    list_display = ("GV_key","id")
    ordering = ("id",)     