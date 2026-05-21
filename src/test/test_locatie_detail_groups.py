import pytest
from model_bakery import baker

from fblocatie.models import Adres, Locatie
from fblocatie.utils.locatie_detail import get_locatie_detail_groups
from referentie_tabellen.models import DienstverleningsKader, LocatieSoort, Persoon


@pytest.mark.django_db
def test_get_locatie_detail_groups_structure_and_basic_values():
    locatie_soort = LocatieSoort.objects.create(name="Soort X")
    dvk = DienstverleningsKader.objects.create(name="DVK X", dvk_nr=1)

    adres = baker.make(
        Adres,
        straat="Straat",
        postcode="1234AB",
        huisnummer=1,
        woonplaats="Amsterdam",
        map_url="https://example.com/maps",
    )

    locatie = baker.make(
        Locatie,
        pandcode=999,
        naam="Testlocatie",
        afkorting="TL",
        adres=adres,
        locatie_soort=locatie_soort,
        dvk_naam=dvk,
        archief=False,
        vastgoed=None,
    )

    groups = get_locatie_detail_groups(locatie)

    assert isinstance(groups, list)
    titles = [g["title"] for g in groups]
    assert titles == [None, "Algemeen", "Adresgegevens", "Contacten", "Externe koppelingen", "GV", "Overig"]

    algemeen_rows = {r["label"]: r for r in groups[1]["rows"]}
    assert algemeen_rows["Afkorting"]["value"] == "TL"
    assert algemeen_rows["Actief"]["value"] == "Ja"

    adres_rows = {r["label"]: r for r in groups[2]["rows"]}
    assert adres_rows["Straat"]["value"] == "Straat"
    assert adres_rows["Kaart (adres)"]["is_url"] is True
    assert adres_rows["Kaart (adres)"]["value"] == "https://example.com/maps"


@pytest.mark.django_db
def test_get_locatie_detail_groups_formats_m2m_as_list_of_strings_and_empty_as_none():
    locatie_soort = LocatieSoort.objects.create(name="Soort Y")
    dvk = DienstverleningsKader.objects.create(name="DVK Y", dvk_nr=2)

    adres = baker.make(
        Adres,
        straat="Straat",
        postcode="1234AB",
        huisnummer=2,
        woonplaats="Amsterdam",
        map_url="https://example.com/maps",
    )

    locatie = baker.make(
        Locatie,
        pandcode=1000,
        naam="Testlocatie 2",
        afkorting="TL2",
        adres=adres,
        locatie_soort=locatie_soort,
        dvk_naam=dvk,
        vastgoed=None,
    )

    # No related people, so template renders '-'
    groups_empty = get_locatie_detail_groups(locatie)
    contacten_rows_empty = {r["label"]: r for r in groups_empty[3]["rows"]}
    assert contacten_rows_empty["Locatiemanager"]["value"] is None

    # Add related people, so template should render a list of strings
    p1 = Persoon.objects.create(voornaam="A", achternaam="B")
    p2 = Persoon.objects.create(voornaam="C", achternaam="D")
    locatie.loc_manager.add(p1, p2)

    groups = get_locatie_detail_groups(locatie)
    contacten_rows = {r["label"]: r for r in groups[3]["rows"]}

    value = contacten_rows["Locatiemanager"]["value"]
    assert isinstance(value, list)
    assert set(value) == {str(p1), str(p2)}
