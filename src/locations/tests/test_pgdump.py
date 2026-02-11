import csv
import os
import shutil
from unittest.mock import patch

import pytest
from django.core.management import call_command
from model_bakery import baker

from locations.management.commands.pgdump import Command as PgDumpCommand
from locations.models import Location


class TestPgDumpCommand:
    TMP_DIRECTORY = "/tmp/tmp_pgdump"

    @patch("locations.management.commands.pgdump.Command._dump_model_to_csv")
    def test_start_dump(self, mock_dump):
        command = PgDumpCommand()

        mock_file_path = os.path.join(self.TMP_DIRECTORY, "test.csv")
        mock_dump.return_value = mock_file_path

        os.makedirs(self.TMP_DIRECTORY, exist_ok=True)
        with open(mock_file_path, "w") as f:
            f.write("dummy data")

        command.start_dump(["locations"])

        # Assert the temporary directory was created
        assert os.path.isdir(self.TMP_DIRECTORY)

        # Assert _dump_model_to_csv was called
        assert mock_dump.called

        # Cleanup
        shutil.rmtree(self.TMP_DIRECTORY)

    @pytest.mark.django_db
    def test_dump_model_to_csv(self):
        """
        Test that _dump_model_to_csv creates a valid CSV file for a model.
        """
        os.makedirs(self.TMP_DIRECTORY, exist_ok=True)

        baker.make(Location, _quantity=5)

        command = PgDumpCommand()
        filepath = command._dump_model_to_csv(Location)

        assert os.path.isfile(filepath)

        # Read the CSV file and verify its contents
        with open(filepath, "r", encoding="utf-8") as csv_file:
            reader = csv.reader(csv_file)
            rows = list(reader)

        # Verify the header row matches the model's fields
        fields = [field.name for field in Location._meta.fields]
        assert rows[0] == fields

        # Verify the number of rows matches the number of objects in the database
        assert len(rows) - 1 == Location.objects.count()  # Subtract 1 for the header row

        # Cleanup
        os.remove(filepath)
        shutil.rmtree(self.TMP_DIRECTORY)

    @patch("locations.management.commands.pgdump.OverwriteStorage.save_without_postfix")
    def test_upload_to_blob(self, mock_save):
        """
        Test that upload_to_blob uploads each CSV file directly to the root of Azure Storage.
        """
        os.makedirs(self.TMP_DIRECTORY, exist_ok=True)

        # Create dummy CSV files
        csv_files = ["Location.csv", "PropertyGroup.csv"]
        for file_name in csv_files:
            file_path = os.path.join(self.TMP_DIRECTORY, file_name)
            with open(file_path, "w") as f:
                f.write("dummy data")

        command = PgDumpCommand()
        command.upload_to_blob()

        assert mock_save.call_count == len(csv_files)

        for file_name in csv_files:
            found = False
            for call in mock_save.call_args_list:
                kwargs = call.kwargs
                if kwargs["name"] == file_name and hasattr(kwargs["content"], "read"):
                    found = True
                    break
            assert found, f"save_without_postfix was not called with name='{file_name}'"

        # Cleanup
        shutil.rmtree(self.TMP_DIRECTORY)

    def test_remove_dump(self):
        """
        Test that remove_dump deletes the temporary directory.
        """
        os.makedirs(self.TMP_DIRECTORY, exist_ok=True)

        command = PgDumpCommand()
        command.remove_dump()

        # Assert the directory was removed
        assert not os.path.exists(self.TMP_DIRECTORY)

    @pytest.mark.django_db
    @patch("locations.management.commands.pgdump.OverwriteStorage.save_without_postfix")
    def test_pg_dump_command(self, mock_save):
        """
        Test the entire pgdump command end-to-end.
        """
        baker.make(Location, name="TEST")

        call_command("pgdump")

        # Assert the temporary directory was removed
        assert not os.path.isdir(self.TMP_DIRECTORY)
