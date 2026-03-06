import csv

from django.contrib import messages
from django.core.exceptions import ValidationError

from locations.processors import LocationProcessor

from .importer import ImporterProcessCSV


def handle_import_csv(request, csv_file) -> int:
    """Process an uploaded CSV file and add Django messages for feedback.

    Returns the number of locations added (best-effort; currently 0).
    """
    location_added = 0

    if not csv_file or not csv_file.name.endswith(".csv"):
        messages.add_message(
            request, messages.ERROR, f"{getattr(csv_file, 'name', 'Bestand')} is geen gelding CSV bestand."
        )
        return location_added

    try:
        csv_reader = csv_file.read().decode("utf-8-sig").splitlines()
        csv_dialect = csv.Sniffer().sniff(sample=csv_reader[0], delimiters=";")
    except Exception:
        message = "De locaties kunnen niet ingelezen worden. Zorg ervoor dat je ';' als scheidingsteken en UTF-8 als codering gebruikt."
        messages.add_message(request, messages.ERROR, message)
        return location_added

    csv_dict = csv.DictReader(csv_reader, dialect=csv_dialect, restval="missing", restkey="excess")

    # Report columns that will be processed during import
    location_properties = set(LocationProcessor().location_properties)
    headers = set(csv_dict.fieldnames or [])

    used_columns = list(headers & location_properties)
    message = f"Kolommen {used_columns} worden verwerkt."
    messages.add_message(request, messages.INFO, message)

    # Process the rows from the import file
    importer = ImporterProcessCSV()
    for i, row in enumerate(csv_dict):
        # Check if a row is missing a value/column
        if "missing" in row.values():
            message = f"Rij {i+1} is niet verwerkt want deze mist een kolom"
            messages.add_message(request, messages.WARNING, message)
            continue

        # Check if a row has too many values/columns
        if row.get("excess"):
            message = f"Rij {i+1} is niet verwerkt want deze heeft teveel kolommen"
            messages.add_message(request, messages.WARNING, message)
            continue

        try:
            importer.main(row)
        except ValidationError as err:
            importer.errors["main"] = f"Error in main: {err}"

        if importer.errors:
            message = f"Fout importeren locatie {importer.locatie_id}: {importer.errors}"
            messages.add_message(request, messages.ERROR, message)

    return location_added
