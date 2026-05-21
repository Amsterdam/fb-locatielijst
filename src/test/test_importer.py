import pytest

from import_export_csv.importer import ImporterProcessCSV
from referentie_tabellen.models import Persoon


def test_get_persoon_none():
    obj, err = ImporterProcessCSV._get_persoon(None)
    assert obj is None
    assert err is None


@pytest.mark.django_db
def test_get_persoon_existing():
    p = Persoon.objects.create(voornaam="Jan", achternaam="Jansen")
    obj, err = ImporterProcessCSV._get_persoon("Jan Jansen")
    assert err is None
    assert obj == p


@pytest.mark.django_db
def test_get_persoon_not_found():
    obj, err = ImporterProcessCSV._get_persoon("Non Existent")
    assert obj is None
    assert isinstance(err, tuple)
    assert err[0] == "Non Existent"
    assert isinstance(err[1], Persoon.DoesNotExist)


@pytest.mark.django_db
def test_get_persoon_invalid_format():
    obj, err = ImporterProcessCSV._get_persoon("SingleName")
    assert obj is None
    assert isinstance(err, tuple)
    assert err[0] == "SingleName"
    assert isinstance(err[1], ValueError)


@pytest.mark.parametrize(
    "name",
    [
        "Jan Jansen / Piet Jansen",
        "Jan Jansen/Piet Jansen",
        "Jan Jansen|Piet Jansen",
    ],
)
@pytest.mark.django_db
def test_get_persoon_duo_persons(name):
    obj, err = ImporterProcessCSV._get_persoon(name)
    assert obj is None
    assert isinstance(err, tuple)
    assert err[0] == name
    assert isinstance(err[1], Persoon.DoesNotExist)


@pytest.mark.django_db
def test_get_referentietabellen_fields_persoon_none_skipped():
    importer = ImporterProcessCSV()
    referentie_tabellen = [("persoon_field", Persoon)]
    data = {"persoon_field": None}
    result = importer.get_referentietabellen_fields(referentie_tabellen, data.copy())
    assert result["persoon_field"] is None
    assert importer.error_list == []


@pytest.mark.parametrize(
    "names, expected",
    [
        ("Jan Jansen / Piet Jansen", "Jan Jansen / Piet Jansen"),
        ("Jan Jansen/Piet Jansen", "Jan Jansen/Piet Jansen"),
        ("Jan Jansen|Piet Jansen", "Piet Jansen"),
    ],
)
@pytest.mark.django_db
def test_get_many_to_many_duo_persons(names, expected):
    importer = ImporterProcessCSV()
    Persoon.objects.create(voornaam="Jan", achternaam="Jansen")

    result = importer._get_many_to_many(Persoon, names, sep="|")

    assert isinstance(result, list)
    assert importer.error_list[0][0] == expected
    assert isinstance(importer.error_list[0][1], Persoon.DoesNotExist)
