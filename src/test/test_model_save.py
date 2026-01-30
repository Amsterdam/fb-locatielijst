import pytest
from django.core.exceptions import ValidationError
from model_bakery import baker

from fblocatie.models import Adres, Locatie, Vastgoed, calc_lat_lon_from_geometry


@pytest.mark.parametrize(
    "test_x, test_y, expected",
    [
        (
            122324,
            487928,
            {"lat": 52.378247, "lon": 4.907321},
        )
    ],
)
def test_calc_lat_lon_from_geometry(test_x, test_y, expected):
    """Calculate latitude and longitude (srid=4326; WGS coordinates) from given srid=28992 (RD-coordinates)"""
    dict = calc_lat_lon_from_geometry(test_x, test_y)
    assert round(dict["lat"], 6) == expected["lat"]
    assert round(dict["lon"], 6) == expected["lon"]


@pytest.mark.parametrize(
    "test_x, test_y, expected",
    [
        (
            122324,
            487928,
            {"lat": 52.378247, "lon": 4.907321},
        ),
        (
            131508.00,
            479894.00,
            {"lat": 52.306511, "lon": 5.042756},
        ),
        (
            None,
            487928,
            {"lat": None, "lon": None},
        ),
        (
            "122324",
            487928,
            {"lat": 52.378247, "lon": 4.907321},
        ),
    ],
)
@pytest.mark.django_db
def test_save_iflatlon(test_x, test_y, expected):
    """consistency:  calculate lat,lon from given rd_x and rd_y"""
    adres = baker.make(Adres, rd_x=test_x, rd_y=test_y)

    assert Adres.objects.last().rd_y == test_y
    assert Adres.objects.last().lat == expected["lat"]
    assert Adres.objects.last().lon == expected["lon"]
    adres.delete()
    assert Adres.objects.count() == 0


@pytest.mark.django_db
def test_clean_vastgoed_valid():
    adres1 = baker.make(Adres)
    vastgoed1 = baker.make(Vastgoed, adres=adres1)

    locatie1 = baker.make(Locatie, vastgoed=vastgoed1, adres=adres1)

    try:
        locatie1.clean()
    except ValidationError:
        pytest.fail("clean() raised ValidationError unexpectedly!")


@pytest.mark.django_db
def test_clean_vastgoed_invalid():
    adres1 = baker.make(Adres)
    adres2 = baker.make(Adres)
    vastgoed2 = baker.make(Vastgoed, adres=adres2)

    locatie2 = baker.prepare(Locatie, vastgoed=vastgoed2, adres=adres1)

    with pytest.raises(ValidationError) as excinfo:
        locatie2.clean()

    assert str(excinfo.value) == "['Het geselecteerde vastgoed behoort niet tot het geselecteerde adres.']"


# TODO: onderstaande test goed maken
# def test_save_vastgoed_matching_adres(self):
#     """ Check if vastgoed.adres=None and there is a matching adres it adopts """
#     adres3 = baker.make(Adres)
#     vastgoed3 = baker.make(Vastgoed, adres = None)
#     locatie3 = baker.prepare(Locatie, vastgoed=vastgoed3, adres=adres3)

#     locatie3.save()
#     assert locatie3.vastgoed == adres3
