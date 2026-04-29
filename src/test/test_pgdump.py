import csv
import io
import os
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.http import HttpResponse
from model_bakery import baker

from fblocatie.management.commands.pgdump import Command as PgDumpCommand
from fblocatie.models import Adres, Locatie
from referentie_tabellen.models import DienstverleningsKader, LocatieSoort


class TestPgDumpCommand:
	@pytest.fixture()
	def command(self, tmp_path):
		command = PgDumpCommand()
		command.TMP_DIRECTORY = str(tmp_path / "tmp_pgdump")
		command.EXPORT_FILE_NAME = "all_locations.csv"
		return command

	def _dummy_csv_response(self, content: bytes = b"\xef\xbb\xbfcol_a;col_b\n1;2\n"):
		response = HttpResponse(content_type="text/csv; charset=utf-8")
		response.write(content)
		return response

	@pytest.mark.django_db
	def test_create_export_csv(self, command):
		locatie_soort = LocatieSoort.objects.create(name="Soort 1")
		dvk = DienstverleningsKader.objects.create(name="DVK 1", dvk_nr=1)

		adres = baker.make(
			Adres,
			straat="Straat 1",
			postcode="1234AB",
			huisnummer=1,
			woonplaats="Amsterdam",
			map_url="https://example.com/maps",
		)

		locatie = baker.make(
			Locatie,
			naam="Locatie 1",
			afkorting="L1",
			adres=adres,
			locatie_soort=locatie_soort,
			dvk_naam=dvk,
		)

		command.create_export_csv()

		file_path = os.path.join(command.TMP_DIRECTORY, command.EXPORT_FILE_NAME)
		with open(file_path, "rb") as f:
			decoded = f.read().decode("utf-8-sig")

		reader = csv.DictReader(io.StringIO(decoded), delimiter=";")
		assert reader.fieldnames is not None
		assert "pandcode" in reader.fieldnames
		assert "naam" in reader.fieldnames

		rows = list(reader)
		assert len(rows) == 1
		assert rows[0]["pandcode"] == str(locatie.pandcode)
		assert rows[0]["naam"] == locatie.naam

	@patch("fblocatie.management.commands.pgdump.fetch_locations_for_export")
	@patch("fblocatie.management.commands.pgdump.get_csv_response")
	def test_create_export_csv_writes_single_csv_file(self, mock_get_csv_response, mock_fetch, command):
		mock_fetch.return_value = []
		mock_get_csv_response.return_value = self._dummy_csv_response()

		command.create_export_csv()

		assert os.path.isdir(command.TMP_DIRECTORY)

		file_path = os.path.join(command.TMP_DIRECTORY, command.EXPORT_FILE_NAME)
		assert os.path.isfile(file_path)

		with open(file_path, "rb") as f:
			content = f.read()

		assert content.startswith(b"\xef\xbb\xbf")
		assert b"col_a;col_b" in content

	@patch("fblocatie.management.commands.pgdump.fetch_locations_for_export")
	@patch("fblocatie.management.commands.pgdump.get_csv_response")
	def test_create_export_csv_overwrites_existing_file(self, mock_get_csv_response, mock_fetch, command):
		mock_fetch.return_value = []

		first = self._dummy_csv_response(b"\xef\xbb\xbfcol_a;col_b\nfirst;1\n")
		second = self._dummy_csv_response(b"\xef\xbb\xbfcol_a;col_b\nsecond;2\n")
		mock_get_csv_response.side_effect = [first, second]

		command.create_export_csv()
		command.create_export_csv()

		file_path = os.path.join(command.TMP_DIRECTORY, command.EXPORT_FILE_NAME)
		with open(file_path, "rb") as f:
			content = f.read()

		assert content == second.content

	@patch("fblocatie.management.commands.pgdump.OverwriteStorage.save_without_postfix")
	def test_upload_to_blob_uploads_single_file(self, mock_save, command):
		os.makedirs(command.TMP_DIRECTORY, exist_ok=True)
		file_path = os.path.join(command.TMP_DIRECTORY, command.EXPORT_FILE_NAME)
		with open(file_path, "wb") as f:
			f.write(b"dummy")

		command.upload_to_blob()

		assert mock_save.call_count == 1
		kwargs = mock_save.call_args.kwargs
		assert kwargs["name"] == command.EXPORT_FILE_NAME
		assert hasattr(kwargs["content"], "read")

	def test_remove_dump_deletes_temporary_directory(self, command):
		os.makedirs(command.TMP_DIRECTORY, exist_ok=True)
		command.remove_dump()

		assert not os.path.exists(command.TMP_DIRECTORY)

	@patch("fblocatie.management.commands.pgdump.fetch_locations_for_export")
	@patch("fblocatie.management.commands.pgdump.get_csv_response")
	@patch("fblocatie.management.commands.pgdump.OverwriteStorage.save_without_postfix")
	def test_pgdump_command_end_to_end(self, mock_save, mock_get_csv_response, mock_fetch, tmp_path):
		# Patch the command's temp directory to keep the test isolated.
		tmp_directory = str(tmp_path / "tmp_pgdump")
		with patch.object(PgDumpCommand, "TMP_DIRECTORY", tmp_directory), patch.object(
			PgDumpCommand, "EXPORT_FILE_NAME", "all_locations.csv"
		):
			mock_fetch.return_value = []
			mock_get_csv_response.return_value = self._dummy_csv_response()

			call_command("pgdump")

		assert mock_save.call_count == 1
		assert not os.path.isdir(tmp_directory)
