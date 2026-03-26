import csv
from django.http import HttpResponse
from django.utils import timezone

from .mappings import (
    ADRES_MAPPING,
    LOCATIE_MANY_TO_MANY_FIELDS,
    LOCATIE_MAPPING,
    LOCATIE_REFERENTIE_TABELLEN,
    VG_MAPPING,
    VG_REFERENTIE_TABELLEN,
)
from fblocatie.models import Locatie


def fetch_locations_for_export():
    return Locatie.objects.select_related(
        "adres",
        "vastgoed",
        *[field for field, _ in LOCATIE_REFERENTIE_TABELLEN],
        *[f"vastgoed__{field}" for field, _ in VG_REFERENTIE_TABELLEN],
    ).prefetch_related(
        *[field for field, _ in LOCATIE_MANY_TO_MANY_FIELDS]
    )


def build_csv_row(locatie) -> dict:
    row = {}

    for model_field, csv_column in LOCATIE_MAPPING.items():
        if any(model_field == field for field, _ in LOCATIE_MANY_TO_MANY_FIELDS):
            row[csv_column] = " | ".join(str(item) for item in getattr(locatie, model_field).all())
        else:
            row[csv_column] = getattr(locatie, model_field, "") or ""

    adres = getattr(locatie, "adres", None)
    for model_field, csv_column in ADRES_MAPPING.items():
        row[csv_column] = getattr(adres, model_field, "") or "" if adres else ""

    vastgoed = getattr(locatie, "vastgoed", None)
    for model_field, csv_column in VG_MAPPING.items():
        row[csv_column] = getattr(vastgoed, model_field, "") or "" if vastgoed else ""

    return row


def get_csv_response(locations) -> HttpResponse:
    date = timezone.localtime(timezone.now()).strftime("%Y-%m-%d_%H.%M")

    response = HttpResponse(
        content_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="locaties_export_{date}.csv"'},
    )
    response.write("\ufeff".encode("utf-8"))

    all_columns = list(LOCATIE_MAPPING.values()) + list(ADRES_MAPPING.values()) + list(VG_MAPPING.values())
    writer = csv.DictWriter(response, fieldnames=all_columns, delimiter=";")
    writer.writeheader()

    for locatie in locations:
        writer.writerow(build_csv_row(locatie))

    return response