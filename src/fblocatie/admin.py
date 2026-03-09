from django.contrib import admin

from fblocatie.models import Adres, Locatie, Vastgoed

admin.site.site_header = "FB Locatielijst"
admin.site.index_title = "Beheer"
admin.site.site_title = "FB Locatielijst - Beheer"


@admin.register(Locatie)
class LocatieAdmin(admin.ModelAdmin):
    change_list_template = "fblocatie/locatie_changelist.html"

    list_display = ("afkorting", "pandcode", "naam", "dvk_naam", "locatie_soort", "vastgoed__bezit", "archief")
    ordering = ("pandcode",)
    search_fields = ("afkorting", "naam", "pandcode")
    autocomplete_fields = [
        "adres",
        "bezoekadres",
        "loc_manager",
        "loc_coordinator",
        "contact_dir",
        "tom",
        "tsc",
        "beveiliging",
        "veiligheid",
    ]
    search_help_text = "zoek op afkorting, naam of pandcode"

    list_filter = ("archief", "dvk_naam", "locatie_soort", "vastgoed__bezit", "locatieteam")
    readonly_fields = ["pandcode", "archief_datum"]

    def get_fieldsets(self, request, obj=None):
        all_fields = [field.name for field in self.model._meta.get_fields() if getattr(field, "editable", False)]

        controlled_fields = ["pandcode"]
        koppel_fields = ["pas_loc", "pas_lc", "anet_loc", "emobj", "po", "priva_gbs"]
        loc_fields = [
            "locatieteam",
            "loc_email",
            "loc_tel",
            "loc_manager",
            "loc_coordinator",
            "contact_dir",
            "tom",
            "tsc",
            "beveiliging",
            "veiligheid",
            "perceel_installateur",
        ]
        closing_fields = ["notitie"]
        remaining_fields = [
            field
            for field in all_fields
            if field not in (controlled_fields + loc_fields + closing_fields + koppel_fields)
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
                "Locatieteamvelden",
                {
                    "fields": loc_fields,
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


@admin.register(Adres)
class AdresAdmin(admin.ModelAdmin):
    list_display = (
        "vot_id",
        "postcode",
        "straat",
        "huisnummer",
        "huisletter",
        "huisnummertoevoeging",
        "woonplaats",
        "id",
    )
    ordering = (
        "straat",
        "huisnummer",
        "huisletter",
        "huisnummertoevoeging",
    )
    readonly_fields = ("lat", "lon", "map_url")

    search_fields = ("postcode", "straat", "woonplaats")
    search_help_text = "zoek op woonplaats, straat of postcode"


@admin.register(Vastgoed)
class VastgoedAdmin(admin.ModelAdmin):
    list_display = ("GV_key", "adres", "bezit", "bouwjaar", "id")
    ordering = ("adres__straat",)
    list_filter = ("bezit",)
    search_fields = ("adres__straat", "adres__woonplaats")
