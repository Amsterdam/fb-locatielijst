from django.contrib import admin

from fblocatie.models import Adres, Locatie, LocatieTeam, Vastgoed


@admin.register(Locatie)
class LocatieAdmin(admin.ModelAdmin):
    change_list_template = "fblocatie/locatie_changelist.html"

    list_display = ("afkorting", "pandcode", "naam", "dvk_naam", "locatie_soort", "vastgoed__bezit", "archief")
    ordering = ("pandcode",)
    search_fields = ("afkorting", "naam", "pandcode")
    search_help_text = "zoek op afkorting, naam of pandcode"

    list_filter = ("archief",  "dvk_naam", "locatie_soort", "vastgoed__bezit", "locatieteam")
    readonly_fields = ["pandcode", "archief_datum"]

    def get_fieldsets(self, request, obj=None):
        all_fields = [field.name for field in self.model._meta.get_fields() if getattr(field, "editable", False)]

        controlled_fields = ["pandcode"]
        koppel_fields = ["pas_loc", "pas_lc", "anet_loc", "emobj", "po", "priva_gbs"]
        closing_fields = ["notitie"]
        remaining_fields = [
            field for field in all_fields if field not in (controlled_fields + closing_fields + koppel_fields)
        ]

        fieldsets = (
            (
                None,
                {
                    "fields": controlled_fields,
                },
            ),
            (
                None,
                {
                    "fields": remaining_fields,
                },
            ),
            (
                None,
                {
                    "fields": closing_fields,
                },
            ),
            (
                "Koppelvelden",
                {
                    "fields": koppel_fields,
                },
            ),
        )
        return fieldsets


@admin.register(LocatieTeam)
class LocatieTeamAdmin(admin.ModelAdmin):
    list_display = ("nummer", "email", "loc_manager", "id")
    ordering = ("id",)


@admin.register(Adres)
class AdresAdmin(admin.ModelAdmin):
    list_display = ("vot_id", "postcode", "straat", "huisnummer", "huisletter", "huisnummertoevoeging", "id")
    ordering = (
        "straat",
        "huisnummer",
        "huisletter",
        "huisnummertoevoeging",
        "id",
    )
    readonly_fields = ("lat", "lon", "map_url")

    search_fields = ("postcode", "straat", "woonplaats")
    search_help_text = "zoek op woonplaats, straat of postcode"


@admin.register(Vastgoed)
class VastgoedAdmin(admin.ModelAdmin):
    list_display = ("GV_key", "adres", "bezit", "bouwjaar", "id")
    ordering = ("id",)
    list_filter = ("bezit",)
