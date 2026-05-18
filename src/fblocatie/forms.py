from django import forms


class LocatieListForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        property_choices = [
            ("", "Alle tekstvelden"),
            ("naam", "Naam"),
            ("pandcode", "Pandcode"),
            ("afkorting", "Afkorting"),
            ("beschrving", "Beschrijving"),
            ("ambtenaar", "Gemeentelijke huisvesting"),
            ("soort", "Soort locatie"),
            ("werkplek", "Aantal werkplekken"),
            ("lt", "Locatieteam"),
            ("lt_mail", "Mailadres locatieteam"),
            ("dvk_naam", "Categorie dienstverleningskader"),
            ("budget_dir", "Budget verantwoordelijke directie"),
            ("routecode", "Routecode indien geen budget FB"),
            ("themagv", "Themaportefeuille GV"),
            ("vlekken", "Directies in het pand"),
            ("straat", "Straat"),
            ("postcode", "Postcode"),
            ("huisnummer", "Huisnummer"),
            ("huisletter", "Huisletter"),
            ("numtoeg", "Nummer toevoeging"),
            ("plaats", "Plaats"),
            ("maps", "Locatie op kaart"),
            ("adrs_toeg", "Afwijkend adres"),
            ("adres2_rol", "Functie afwijkend adres"),
            ("lm", "Locatiemanager"),
            ("lc", "Locatiecoördinator"),
            ("contact", "Contactpersoon vanuit directies"),
            ("tom", "Technisch objectmanager (TOM)"),
            ("tsc", "Technisch service coördinator(TSC)"),
            ("beveiligng", "Adviseur beveiliging"),
            ("veiligheid", "Adviseur veiligheid"),
            ("am_gv", "Assetmanager/contact vastgoed"),
            ("plgv", "Projectleider Gemeentelijk vastgoed"),
            ("ew", "E&W perceel installateur"),
            ("voorz", "Voorzieningen"),
            ("kantoorart", "Kantoorartikelkast uitgebreid assortiment"),
            ("contract", "Contracten op deze locatie"),
            ("gv", "GV locatiecode (Planon)"),
            ("bezit", "Eigendom / Huur"),
            ("bouwjaar", "Bouwjaar"),
            ("vvo", "Verhuurbaar vloeroppervlak (VVO)"),
            ("bvo", "Bruto vloeroppervlakte (BVO)"),
            ("energielbl", "Energielabel"),
            ("mon_gem", "Monument status Amsterdam"),
            ("mon_brkpb", "Monument status"),
        ]

        self.fields["property"] = forms.ChoiceField(
            label="Waar wil je zoeken",
            choices=property_choices,
            widget=forms.Select(),
            required=False,
        )

        self.fields["search"] = forms.CharField(
            label="Wat wil je zoeken",
            required=False,
            widget=forms.TextInput(attrs={"autocomplete": "off"}),
        )

        self.fields["archive"] = forms.ChoiceField(
            label="Archief",
            choices=[("active", "Actief"), ("archived", "Gearchiveerd"), ("all", "Alle")],
            required=False,
        )
