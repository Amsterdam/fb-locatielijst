import pytest

from referentie_tabellen.models import Persoon
from import_export_csv.importer import ImporterProcessCSV


def test_get_persoon_none():
    obj, err = ImporterProcessCSV._get_persoon(None)
    assert obj is None
    assert err == ""


@pytest.mark.django_db
def test_get_persoon_existing():
    p = Persoon.objects.create(voornaam="Jan", achternaam="Jansen")
    obj, err = ImporterProcessCSV._get_persoon("Jan Jansen")
    assert err == ""
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
    ],
)
@pytest.mark.django_db
def test_get_persoon_duo_persons(name):
    obj, err = ImporterProcessCSV._get_persoon(name)
    assert obj is None
    assert isinstance(err, tuple)
    assert err[0] == name
    assert isinstance(err[1], Persoon.DoesNotExist)