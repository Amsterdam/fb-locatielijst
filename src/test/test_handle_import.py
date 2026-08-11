from unittest.mock import MagicMock, patch

import pytest
from django.contrib import messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import ValidationError
from django.core.management import call_command

from import_export_csv.handle_import import handle_import_csv


def _build_request():
    request = MagicMock()
    request.session = {}
    message_storage = FallbackStorage(request)
    setattr(request, "_messages", message_storage)
    return request, message_storage


def _build_file(name: str, content: str):
    fake_file = MagicMock()
    fake_file.name = name
    fake_file.read.return_value = content.encode("utf-8-sig")
    return fake_file


@pytest.mark.django_db
def test_handle_import_csv_with_fake_file():
    # Load the referentie_tabellen fixture
    call_command("loaddata", "src/referentie_tabellen/fixtures/referentie_tabellen.json")

    # Prepare a realistic CSV file with two rows
    csv_content = (
        "pandcode;naam;afkorting;beschrving;actief;mut_datum;afstoten;ambtenaar;soort;werkplek;"
        "gelieerd;lt;lt_mail;dvk_nr;dvk_naam;budget_dir;routecode;themagv;vlekken;bagconf;straat;"
        "postcode;huisnummer;huisletter;numtoeg;plaats;longitude;latitude;rd_x;rd_y;maps;adrs_toeg;"
        "adres2_rol;adres2_lat;adres2_lon;lm;lc;contact;tom;tsc;beveiligng;veiligheid;am_gv;plgv;ew;"
        "voorz;kantoorart;contract;netn;emobj;vbo_id;gv;gv_id;gv_grp;pasloc;priva_gbs;po;pas;anet;"
        "bezit;bouwjaar;vvo;bvo;energielbl;mon_gem;mon_brkpb;notitie;bag_id;pas_loc;anet_loc;"
        "aangemaakt;gewijzigd;archief\n"
        "24006;Anton De Komplein 150;ADK150;Stadskantoor;Ja;;;Ja;Kantoor;772;;4;facilitairbureau.sdzo@amsterdam.nl;"
        "1;Basis;Griffie;FB;Gemeentelijke Huisvesting;Staf Stadsdelen, Beheer en Dienstverlening (Directie)|_anders;"
        "ja;Anton de Komplein;1102CW;150;;;Amsterdam;52.316241;4.956475;125630;481008;"
        "https://maps.google.com/?q=52.316241,4.956475;;;;;Test-test Test;Test2 Test2;;;;;"
        "Test-test Test|Test2 Test2;Test-test Test;Test2 Test2;Perceel 1 Spie;"
        "Bedrijfsrestaurant|Beeldbelplekken|Bekers voor bezoek|Fietsenstalling|Gehandicaptentoiletten|"
        "Kolf- en rustruimte|Parkeerplaatsen|Rolstoeltoegankelijkheid|LED-verlichting;"
        "Verdieping 3 (de knik);Catering & Banqueting|Warme dranken;AKP;10195;;2519;O-00866;gebouwen;ADK150;"
        "Stadsdeel Z-O;6;A;Ja;Eigendom;2006;11049;12463;A;geen monument;geen monument;;0363100012078772;"
        "ADK150;AKP;27-01-2025;29-10-2025 08:26;True\n"
    )
    fake_file = _build_file("fake_test_record.csv", csv_content)

    # Prepare a fake request with messages
    request, message_storage = _build_request()

    # Call the function
    result = handle_import_csv(request, fake_file)

    # Check that the result is int (should be 0 as per implementation)
    assert isinstance(result, int)
    assert result == 0

    # Check that at least one info message was added
    info_messages = [m for m in message_storage if m.level == messages.INFO]
    assert info_messages, "No info messages found"

    # Check that the processed columns message is present
    assert any("Kolommen" in m.message for m in info_messages)

    # Check that no error or warning messages about missing/excess columns
    error_messages = [m for m in message_storage if m.level == messages.ERROR]
    warning_messages = [m for m in message_storage if m.level == messages.WARNING]
    assert not error_messages, f"Unexpected error messages: {[m.message for m in error_messages]}"
    assert not warning_messages, f"Unexpected warning messages: {[m.message for m in warning_messages]}"


def test_handle_import_csv_rejects_non_csv_file():
    fake_file = _build_file("locations.txt", "pandcode;naam\n1;Test\n")
    request, message_storage = _build_request()

    result = handle_import_csv(request, fake_file)

    assert result == 0
    error_messages = [m.message for m in message_storage if m.level == messages.ERROR]
    assert error_messages == ["locations.txt is geen geldig CSV bestand."]


def test_handle_import_csv_rejects_invalid_payload():
    fake_file = _build_file("locations.csv", "")
    request, message_storage = _build_request()

    result = handle_import_csv(request, fake_file)

    assert result == 0
    error_messages = [m.message for m in message_storage if m.level == messages.ERROR]
    assert error_messages == [
        "De locaties kunnen niet ingelezen worden. Zorg ervoor dat je ';' "
        "als scheidingsteken en UTF-8 als codering gebruikt."
    ]


@patch("import_export_csv.handle_import.ImporterProcessCSV")
def test_handle_import_csv_warns_on_missing_columns(importer_cls):
    fake_file = _build_file("locations.csv", "pandcode;naam\n1\n")
    request, message_storage = _build_request()

    result = handle_import_csv(request, fake_file)

    assert result == 0
    importer_cls.return_value.main.assert_not_called()
    warning_messages = [m.message for m in message_storage if m.level == messages.WARNING]
    assert warning_messages == ["Rij 1 is niet verwerkt want deze mist een kolom"]


@patch("import_export_csv.handle_import.ImporterProcessCSV")
def test_handle_import_csv_warns_on_excess_columns(importer_cls):
    fake_file = _build_file("locations.csv", "pandcode;naam\n1;Test;extra\n")
    request, message_storage = _build_request()

    result = handle_import_csv(request, fake_file)

    assert result == 0
    importer_cls.return_value.main.assert_not_called()
    warning_messages = [m.message for m in message_storage if m.level == messages.WARNING]
    assert warning_messages == ["Rij 1 is niet verwerkt want deze heeft teveel kolommen"]


@patch("import_export_csv.handle_import.ImporterProcessCSV")
def test_handle_import_csv_reports_validation_error(importer_cls):
    importer = importer_cls.return_value
    importer.locatie_id = "LOC-1"
    importer.errors = {}
    importer.main.side_effect = ValidationError("ongeldige rij")

    fake_file = _build_file("locations.csv", "pandcode;naam\n1;Test\n")
    request, message_storage = _build_request()

    result = handle_import_csv(request, fake_file)

    assert result == 0
    error_messages = [m.message for m in message_storage if m.level == messages.ERROR]
    assert len(error_messages) == 1
    assert "Fout importeren locatie LOC-1:" in error_messages[0]
    assert "ongeldige rij" in error_messages[0]


@patch("import_export_csv.handle_import.ImporterProcessCSV")
def test_handle_import_csv_reports_importer_errors(importer_cls):
    importer = importer_cls.return_value
    importer.locatie_id = "LOC-2"
    importer.errors = {}

    def _set_errors(_row):
        importer.errors = {"locatie": ["kapot"]}

    importer.main.side_effect = _set_errors

    fake_file = _build_file("locations.csv", "pandcode;naam\n1;Test\n")
    request, message_storage = _build_request()

    result = handle_import_csv(request, fake_file)

    assert result == 0
    error_messages = [m.message for m in message_storage if m.level == messages.ERROR]
    assert error_messages == ["Fout importeren locatie LOC-2: {'locatie': ['kapot']}"]
