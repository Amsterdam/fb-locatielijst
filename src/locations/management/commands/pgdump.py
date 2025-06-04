import os
import shutil
import csv
import zipfile
from io import StringIO
from django.apps import apps
from django.conf import settings
from django.utils.module_loading import import_string as get_storage_class
from django.core.management.base import BaseCommand
from storages.backends.azure_storage import AzureStorage


class OverwriteStorage:
    """ Set storage to pgdump container
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

    def handle(self, *args, **kwargs):
        app_names = kwargs.get("apps", ["locations"])

        self.start_dump(app_names)

        self.upload_to_blob()

        self.remove_dump()

        self.stdout.write("Data dump completed successfully.")

    def start_dump(self, app_names):
        """
        Dump all models in the specified apps to CSV files and compress them into a ZIP archive.
        """
        os.makedirs(self.TMP_DIRECTORY, exist_ok=True)

        with zipfile.ZipFile(os.path.join(self.TMP_DIRECTORY, "pgdump.zip"), "w") as zip_file:
            for app in app_names:
                for model in apps.get_app_config(app).get_models():
                    csv_filepath = self._dump_model_to_csv(model)
                    zip_file.write(csv_filepath, os.path.basename(csv_filepath))

    def _dump_model_to_csv(self, model):
        """
        Dump a single model's data to a CSV file.
        """
        table_name = model._meta.db_table
        filepath = os.path.join(self.TMP_DIRECTORY, f"{table_name}.csv")

        with open(filepath, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)

            # Write header (field names)
            fields = [field.name for field in model._meta.fields]
            writer.writerow(fields)

            # Write data rows
            for instance in model.objects.all():
                writer.writerow([getattr(instance, field) for field in fields])

        return filepath

    def upload_to_blob(self):
        """
        Upload the ZIP file to Azure Storage.
        """
        storage = OverwriteStorage()
        zip_filepath = os.path.join(self.TMP_DIRECTORY, "pgdump.zip")

        with open(zip_filepath, "rb") as f:
            storage.save_without_postfix(name=os.path.join("pgdump", "pgdump.zip"), content=f)

        self.stdout.write(f"Successfully uploaded {zip_filepath} to Azure Storage.")

    def remove_dump(self):
        """
        Remove the temporary directory and its contents.
        """
        shutil.rmtree(self.TMP_DIRECTORY)