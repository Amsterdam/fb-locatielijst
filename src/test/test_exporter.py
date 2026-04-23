import csv
import io
from datetime import date

import pytest
from django.db.models.query import QuerySet
from model_bakery import baker

import import_export_csv.exporter as exporter
from fblocatie.models import Adres, Locatie, Vastgoed
from import_export_csv.mappings import (
    ADRES_MAPPING,
    EXPORT_ONLY_ADRES_MAPPING,
    LOCATIE_MANY_TO_MANY_FIELDS,
    LOCATIE_MAPPING,
    VG_MAPPING,
)
from referentie_tabellen.models import (
    Contract,
    DienstverleningsKader,
    Directie,
    LocatieBezit,
    LocatieSoort,
    Persoon,
    Voorziening,
)


def _expected_columns():
    return list(LOCATIE_MAPPING.values()) + \
        list(ADRES_MAPPING.values()) + \
        list(EXPORT_ONLY_ADRES_MAPPING.values()) + \
        list(VG_MAPPING.values())


def _parse_csv_response(response):
    decoded = response.content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded), delimiter=";")
    return reader.fieldnames, list(reader)


def _make_locatie(*, naam="Locatie", pandcode=1, adres_kwargs=None, locatie_kwargs=None):
    adres_kwargs = adres_kwargs or {}
    locatie_kwargs = locatie_kwargs or {}

    locatie_soort = LocatieSoort.objects.create(name=f"Soort {pandcode}")
    dvk = DienstverleningsKader.objects.create(name=f"DVK {pandcode}", dvk_nr=pandcode)

    adres = baker.make(
        Adres,
        straat=f"Straat {pandcode}",
        postcode="1234AB",
        huisnummer=pandcode,
        woonplaats="Amsterdam",
        map_url="https://example.com/maps",
        **adres_kwargs,
    )

    locatie = baker.make(
        Locatie,
        pandcode=pandcode,
        naam=naam,
        afkorting=f"L{pandcode}",
        adres=adres,
        locatie_soort=locatie_soort,
        dvk_naam=dvk,
        **locatie_kwargs,
    )

    return locatie


@pytest.mark.django_db
@pytest.mark.parametrize(
    "csv_column",
    [
        LOCATIE_MAPPING["beschrijving"],
        LOCATIE_MAPPING["afstoten"],
        ADRES_MAPPING["huisletter"],
        ADRES_MAPPING["huisnummertoevoeging"],
    ],
)
def test_build_csv_row_emits_empty_string_for_null_fields(csv_column):
    locatie = _make_locatie(pandcode=10, naam="Null fields")

    row = exporter.build_csv_row(locatie)

    assert set(row.keys()) == set(_expected_columns())
    assert row[csv_column] == ""


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field_name, model",
    [
        ("pand_directies", Directie),
        ("voorzieningen", Voorziening),
        ("contracten", Contract),
        ("loc_manager", Persoon),
    ],
)
def test_build_csv_row_m2m_fields_export_empty_or_pipe_joined(field_name, model):
    locatie = _make_locatie(pandcode=20, naam=f"M2M {field_name}")

    csv_column = LOCATIE_MAPPING[field_name]
    row_empty = exporter.build_csv_row(locatie)
    assert row_empty[csv_column] == ""

    def _make_item(i: int):
        if model is Persoon:
            return model.objects.create(voornaam=f"Voor{i}", achternaam=f"Achter{i}")
        return model.objects.create(name=f"Name {i}")

    a = _make_item(1)
    b = _make_item(2)
    getattr(locatie, field_name).add(a, b)

    row = exporter.build_csv_row(locatie)
    assert " | " in row[csv_column]
    assert set(row[csv_column].split(" | ")) == {str(a), str(b)}


@pytest.mark.django_db
def test_build_csv_row_m2m_fields_list_matches_mapping_constant():
    # Light sanity check: ensures exporter logic stays aligned with mapping config.
    mapping_m2m_fields = {field for field, _ in LOCATIE_MANY_TO_MANY_FIELDS}
    assert mapping_m2m_fields.issubset(set(LOCATIE_MAPPING.keys()))


@pytest.mark.django_db
def test_get_csv_response_roundtrips_special_characters_and_delimiter():
    special_name = 'A;B\nC "D"'
    locatie = _make_locatie(pandcode=30, naam=special_name)

    response = exporter.get_csv_response([locatie])

    assert response["Content-Type"].startswith("text/csv")
    assert response["Content-Disposition"].startswith('attachment; filename="locaties_export_')
    assert response.content.startswith(b"\xef\xbb\xbf")

    fieldnames, rows = _parse_csv_response(response)
    assert fieldnames == _expected_columns()
    assert rows[0]["naam"] == special_name


@pytest.mark.django_db
def test_get_csv_response_writes_multiple_rows_in_input_order_and_formats_dates():
    loc_b = _make_locatie(
        pandcode=41,
        naam="Second",
        locatie_kwargs={"afstoten": date(2030, 1, 2), "archief": True},
    )
    loc_a = _make_locatie(pandcode=40, naam="First")

    response = exporter.get_csv_response([loc_b, loc_a])
    _, rows = _parse_csv_response(response)

    assert [r["pandcode"] for r in rows] == ["41", "40"]
    assert rows[0]["afstoten"] == "2030-01-02"
    assert rows[0]["archief"] == "True"


@pytest.mark.django_db
def test_get_csv_response_exports_vastgoed_fields_when_present():
    locatie = _make_locatie(pandcode=50, naam="With vastgoed")

    bezit = LocatieBezit.objects.create(name="Eigendom")
    Vastgoed.objects.create(adres=locatie.adres, GV_key="GV-XYZ", gv_id="GV-50", bezit=bezit)

    locatie.save()

    response = exporter.get_csv_response([locatie])
    _, rows = _parse_csv_response(response)

    assert rows[0]["gv"] == "GV-XYZ"
    assert rows[0]["gv_id"] == "GV-50"
    assert rows[0]["bezit"] == "Eigendom"


@pytest.mark.django_db
def test_export_includes_locatie_information():
    locatie = _make_locatie(pandcode=60, naam="Happy Flow")

    bezit = LocatieBezit.objects.create(name="Eigendom HF")
    Vastgoed.objects.create(adres=locatie.adres, GV_key="GV-HF", gv_id="GV-60", bezit=bezit)
    locatie.save()

    d1 = Directie.objects.create(name="Directie HF 1")
    d2 = Directie.objects.create(name="Directie HF 2")
    v1 = Voorziening.objects.create(name="Projector")
    c1 = Contract.objects.create(name="Schoonmaak HF")
    p1 = Persoon.objects.create(voornaam="Henk", achternaam="Happypath")

    locatie.pand_directies.add(d1, d2)
    locatie.voorzieningen.add(v1)
    locatie.contracten.add(c1)
    locatie.loc_manager.add(p1)

    response = exporter.get_csv_response([locatie])
    fieldnames, rows = _parse_csv_response(response)

    assert fieldnames == _expected_columns()
    assert len(rows) == 1

    row = rows[0]
    assert row["pandcode"] == "60"
    assert row["naam"] == "Happy Flow"
    assert row["straat"] == "Straat 60"
    assert row["gv"] == "GV-HF"
    assert set(row["vlekken"].split(" | ")) == {"Directie HF 1", "Directie HF 2"}
    assert row["voorz"] == "Projector"
    assert row["contract"] == "Schoonmaak HF"
    assert row["lm"] == "Henk Happypath"


@pytest.mark.django_db
def test_fetch_locations_for_export_returns_queryset():
    qs = exporter.fetch_locations_for_export()
    assert isinstance(qs, QuerySet)


@pytest.mark.django_db
def test__get_field_converts_none_to_empty_string_but_keeps_false():
    class Obj:
        x = None
        y = False

    assert exporter._get_field(Obj(), "x") == ""
    assert exporter._get_field(None, "x") == ""
    assert exporter._get_field(Obj(), "y") is False
