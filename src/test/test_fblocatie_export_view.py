import csv
import io

import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.urls import reverse
from model_bakery import baker

from fblocatie.models import Adres, Locatie
from import_export_csv.views import LocationExportView
from referentie_tabellen.models import DienstverleningsKader, LocatieSoort


def _parse_csv_response(response):
    decoded = response.content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded), delimiter=";")
    return list(reader)


@pytest.mark.django_db
def test_fblocatie_export_view_respects_search_query_params():
    user = User.objects.create(username="staff", is_staff=True)

    soort = LocatieSoort.objects.create(name="Soort")
    dvk1 = DienstverleningsKader.objects.create(name="DVK 1", dvk_nr=1)
    dvk2 = DienstverleningsKader.objects.create(name="DVK 2", dvk_nr=2)

    adres1 = baker.make(
        Adres,
        straat="Straat 1",
        postcode="1234AB",
        huisnummer=1,
        woonplaats="Amsterdam",
        map_url="https://example.com/maps/1",
    )
    adres2 = baker.make(
        Adres,
        straat="Straat 2",
        postcode="1234AB",
        huisnummer=2,
        woonplaats="Amsterdam",
        map_url="https://example.com/maps/2",
    )

    baker.make(
        Locatie,
        pandcode=1,
        naam="Foo locatie",
        afkorting="FOO",
        adres=adres1,
        locatie_soort=soort,
        dvk_naam=dvk1,
        archief=False,
    )
    baker.make(
        Locatie,
        pandcode=2,
        naam="Bar locatie",
        afkorting="BAR",
        adres=adres2,
        locatie_soort=soort,
        dvk_naam=dvk2,
        archief=False,
    )

    rf = RequestFactory()
    url = reverse("import_export_urls:locatie-export")
    request = rf.get(url, {"property": "naam", "search": "Foo"})
    request.user = user

    response = LocationExportView.as_view()(request)

    assert response.status_code == 200
    rows = _parse_csv_response(response)
    assert {row["naam"] for row in rows} == {"Foo locatie"}
