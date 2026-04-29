import csv
import os
import shutil

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.module_loading import import_string as get_storage_class

from import_export_csv.exporter import fetch_locations_for_export, get_csv_response


class OverwriteStorage:
    """Set storage to pgdump container
    and overwrite existing files instead of using hash postfixes."""

    def __init__(self, *args, **kwargs):
        if hasattr(settings, "STORAGES") and "pgdump" in settings.STORAGES:
            storage_class = get_storage_class(settings.STORAGES["pgdump"]["BACKEND"])
            storage_options = settings.STORAGES["pgdump"]["OPTIONS"]
        else:
            storage_class = get_storage_class(settings.STORAGES["default"]["BACKEND"])
            storage_options = {}

        self.storage = storage_class(**storage_options)

    def __getattr__(self, name):
        return getattr(self.storage, name)

    def save_without_postfix(self, name, content):
        if self.storage.exists(name):
            self.storage.delete(name)
        return self.storage.save(name, content)


class Command(BaseCommand):
    help = "Export all models in specified apps to CSV files, compress them into a ZIP, and upload to Azure Storage."

    TMP_DIRECTORY = "/tmp/tmp_pgdump"
    EXPORT_FILE_NAME = "all_locations.csv"

    def handle(self, *args, **kwargs):
        self.create_export_csv()

        self.upload_to_blob()

        self.remove_dump()

        self.stdout.write("Data dump completed successfully.")

    def create_export_csv(self):
        """
        Build the locations CSV export.
        """
        os.makedirs(self.TMP_DIRECTORY, exist_ok=True)

        csv_data = get_csv_response(fetch_locations_for_export()).content
        file_path = os.path.join(self.TMP_DIRECTORY, self.EXPORT_FILE_NAME)
        with open(file_path, "wb") as f:
            f.write(csv_data)

    def upload_to_blob(self):
        """
        Upload the export CSV file to Azure Storage.
        """
        storage = OverwriteStorage()

        file_path = os.path.join(self.TMP_DIRECTORY, self.EXPORT_FILE_NAME)
        with open(file_path, "rb") as f:
            storage.save_without_postfix(name=self.EXPORT_FILE_NAME, content=f)

        self.stdout.write(f"Successfully uploaded {self.EXPORT_FILE_NAME} to Azure Storage.")

    def remove_dump(self):
        """
        Remove the temporary directory and its contents.
        """
        shutil.rmtree(self.TMP_DIRECTORY)
