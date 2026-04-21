import csv

from django.http import HttpResponse
from django.utils import timezone

from fblocatie.models import Locatie

from .mappings import (
    ADRES_MAPPING,
    EXPORT_ONLY_ADRES_MAPPING,
    LOCATIE_MANY_TO_MANY_FIELDS,
    LOCATIE_MAPPING,
    LOCATIE_REFERENTIE_TABELLEN,
    VG_MAPPING,
    VG_REFERENTIE_TABELLEN,
)


def _get_field(obj, field):
    value = getattr(obj, field, None)
    return "" if value is None else value


def fetch_locations_for_export():
    return Locatie.objects.select_related(
        "adres",
        "vastgoed",
        *[field for field, _ in LOCATIE_REFERENTIE_TABELLEN],
        *[f"vastgoed__{field}" for field, _ in VG_REFERENTIE_TABELLEN],
    ).prefetch_related(*[field for field, _ in LOCATIE_MANY_TO_MANY_FIELDS])


def build_csv_row(locatie) -> dict:
    row = {}

    for model_field, csv_column in LOCATIE_MAPPING.items():
        # Join many to many fields with " | " as separator, for the rest just get the field value
        if any(model_field == field for field, _ in LOCATIE_MANY_TO_MANY_FIELDS):
            row[csv_column] = " | ".join(str(item) for item in getattr(locatie, model_field).all())
        else:
            row[csv_column] = _get_field(locatie, model_field)

    adres = getattr(locatie, "adres", None)
    for model_field, csv_column in {**ADRES_MAPPING, **EXPORT_ONLY_ADRES_MAPPING}.items():
        row[csv_column] = _get_field(adres, model_field)

    vastgoed = getattr(locatie, "vastgoed", None)
    for model_field, csv_column in VG_MAPPING.items():
        row[csv_column] = _get_field(vastgoed, model_field)

    return row


def get_csv_response(locations) -> HttpResponse:
    date = timezone.localtime(timezone.now()).strftime("%Y-%m-%d_%H.%M")

    response = HttpResponse(
        content_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="locaties_export_{date}.csv"'},
    )

    # Add BOM to the file; because otherwise Excel won't know what's happening
    response.write("\ufeff".encode("utf-8"))

    all_columns = list(LOCATIE_MAPPING.values()) + list(ADRES_MAPPING.values()) + list(EXPORT_ONLY_ADRES_MAPPING.values()) + list(VG_MAPPING.values())
    writer = csv.DictWriter(response, fieldnames=all_columns, delimiter=";")
    writer.writeheader()

    for locatie in locations:
        writer.writerow(build_csv_row(locatie))

    return response
