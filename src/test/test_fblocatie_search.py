import pytest
from django.contrib.auth.models import User
from model_bakery import baker

from fblocatie.models import Adres, Locatie, Vastgoed
from referentie_tabellen.models import DienstverleningsKader, LocatieBezit, LocatieSoort


@pytest.mark.django_db
def test_locatie_search_filter_default_all_fields_searches_across_configured_fields():
    staff_user = User.objects.create(username="staff", is_staff=True)

    soort1 = LocatieSoort.objects.create(name="Soort 1")
    soort2 = LocatieSoort.objects.create(name="Soort 2")
    dvk1 = DienstverleningsKader.objects.create(name="DVK A", dvk_nr=1)
    dvk2 = DienstverleningsKader.objects.create(name="DVK B", dvk_nr=2)

    bezit1 = LocatieBezit.objects.create(name="Eigendom")
    bezit2 = LocatieBezit.objects.create(name="Huur")

    adres1 = baker.make(
        Adres,
        straat="Damrak",
        postcode="1012LG",
        huisnummer=1,
        woonplaats="Amsterdam",
        map_url="https://example.com/a",
    )
    adres2 = baker.make(
        Adres,
        straat="Amstel",
        postcode="1017AB",
        huisnummer=2,
        woonplaats="Amsterdam",
        map_url="https://example.com/b",
    )

    Vastgoed.objects.create(adres=adres1, bezit=bezit1)
    Vastgoed.objects.create(adres=adres2, bezit=bezit2)

    l1 = baker.make(
        Locatie,
        pandcode=100,
        naam="Stadhuis",
        afkorting="STAD",
        adres=adres1,
        locatie_soort=soort1,
        dvk_naam=dvk1,
        archief=False,
    )
    l2 = baker.make(
        Locatie,
        pandcode=200,
        naam="Stopera",
        afkorting="STO",
        adres=adres2,
        locatie_soort=soort2,
        dvk_naam=dvk2,
        archief=False,
    )

    # Search by abbreviation (all fields)
    qs = Locatie.objects.search_filter({"property": "", "search": "STO"}, user=staff_user)
    assert set(qs.values_list("pandcode", flat=True)) == {l2.pandcode}

    # Search by related DVK name (all fields)
    qs = Locatie.objects.search_filter({"property": "", "search": "DVK A"}, user=staff_user)
    assert set(qs.values_list("pandcode", flat=True)) == {l1.pandcode}

    # Numeric search should include pandcode in default mode
    qs = Locatie.objects.search_filter({"property": "", "search": "100"}, user=staff_user)
    assert set(qs.values_list("pandcode", flat=True)) == {l1.pandcode}

    # Prefix search should match pandcode
    qs = Locatie.objects.search_filter({"property": "", "search": "2"}, user=staff_user)
    assert set(qs.values_list("pandcode", flat=True)) == {l2.pandcode}


@pytest.mark.django_db
def test_locatie_search_filter_property_scopes_search_to_that_field():
    staff_user = User.objects.create(username="staff", is_staff=True)

    soort = LocatieSoort.objects.create(name="Soort")
    dvk_a = DienstverleningsKader.objects.create(name="DVK A", dvk_nr=1)
    dvk_b = DienstverleningsKader.objects.create(name="DVK B", dvk_nr=2)

    bezit = LocatieBezit.objects.create(name="Eigendom")

    adres1 = baker.make(
        Adres,
        straat="Damrak",
        postcode="1012LG",
        huisnummer=1,
        woonplaats="Amsterdam",
        map_url="https://example.com/a",
    )
    adres2 = baker.make(
        Adres,
        straat="Amstel",
        postcode="1017AB",
        huisnummer=2,
        woonplaats="Amsterdam",
        map_url="https://example.com/b",
    )

    Vastgoed.objects.create(adres=adres1, bezit=bezit)
    Vastgoed.objects.create(adres=adres2, bezit=bezit)

    l1 = baker.make(
        Locatie,
        pandcode=111,
        naam="Foo",
        afkorting="DVK A",  # intentionally overlaps dvk name
        adres=adres1,
        locatie_soort=soort,
        dvk_naam=dvk_a,
        archief=False,
    )
    l2 = baker.make(
        Locatie,
        pandcode=222,
        naam="Bar",
        afkorting="DVK B",
        adres=adres2,
        locatie_soort=soort,
        dvk_naam=dvk_b,
        archief=False,
    )

    # Scoped to dvk_naam should ignore matches in afkorting
    qs = Locatie.objects.search_filter({"property": "dvk_naam", "search": "DVK A"}, user=staff_user)
    assert set(qs.values_list("pandcode", flat=True)) == {l1.pandcode}

    # Scoped to pandcode requires digits and matches exactly
    qs = Locatie.objects.search_filter({"property": "pandcode", "search": "222"}, user=staff_user)
    assert set(qs.values_list("pandcode", flat=True)) == {l2.pandcode}

    # Partial pandcode matches should work
    qs = Locatie.objects.search_filter({"property": "pandcode", "search": "22"}, user=staff_user)
    assert set(qs.values_list("pandcode", flat=True)) == {l2.pandcode}

    qs = Locatie.objects.search_filter({"property": "pandcode", "search": "22a"}, user=staff_user)
    assert qs.count() == 0


@pytest.mark.django_db
def test_locatie_search_filter_archive_behavior_staff_vs_nonstaff():
    staff_user = User.objects.create(username="staff", is_staff=True)
    plain_user = User.objects.create(username="plain", is_staff=False)

    soort = LocatieSoort.objects.create(name="Soort")
    dvk = DienstverleningsKader.objects.create(name="DVK", dvk_nr=1)
    bezit = LocatieBezit.objects.create(name="Eigendom")

    adres_active = baker.make(
        Adres,
        straat="Damrak",
        postcode="1012LG",
        huisnummer=1,
        woonplaats="Amsterdam",
        map_url="https://example.com/a",
    )
    adres_archived = baker.make(
        Adres,
        straat="Amstel",
        postcode="1017AB",
        huisnummer=2,
        woonplaats="Amsterdam",
        map_url="https://example.com/b",
    )

    Vastgoed.objects.create(adres=adres_active, bezit=bezit)
    Vastgoed.objects.create(adres=adres_archived, bezit=bezit)

    active = baker.make(
        Locatie,
        pandcode=10,
        naam="Active",
        afkorting="A",
        adres=adres_active,
        locatie_soort=soort,
        dvk_naam=dvk,
        archief=False,
    )
    archived = baker.make(
        Locatie,
        pandcode=20,
        naam="Archived",
        afkorting="B",
        adres=adres_archived,
        locatie_soort=soort,
        dvk_naam=dvk,
        archief=True,
    )

    # Default: only active for everyone
    qs_staff_default = Locatie.objects.search_filter({"property": "", "search": ""}, user=staff_user)
    assert set(qs_staff_default.values_list("pandcode", flat=True)) == {active.pandcode}

    qs_plain_default = Locatie.objects.search_filter({"property": "", "search": ""}, user=plain_user)
    assert set(qs_plain_default.values_list("pandcode", flat=True)) == {active.pandcode}

    # Staff can explicitly request archived/all
    qs_staff_archived = Locatie.objects.search_filter({"archive": "archived"}, user=staff_user)
    assert set(qs_staff_archived.values_list("pandcode", flat=True)) == {archived.pandcode}

    qs_staff_all = Locatie.objects.search_filter({"archive": "all"}, user=staff_user)
    assert set(qs_staff_all.values_list("pandcode", flat=True)) == {active.pandcode, archived.pandcode}

    # Non-staff cannot see archived even if explicitly asked
    qs_plain_all = Locatie.objects.search_filter({"archive": "all"}, user=plain_user)
    assert set(qs_plain_all.values_list("pandcode", flat=True)) == {active.pandcode}
