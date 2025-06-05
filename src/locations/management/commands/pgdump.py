import os
import shutil
import csv
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
        Dump all models in the specified apps to CSV files.
        """
        os.makedirs(self.TMP_DIRECTORY, exist_ok=True)

        for app in app_names:
            for model in apps.get_app_config(app).get_models():
                self._dump_model_to_csv(model)

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
        Upload each CSV file to Azure Storage.
        """
        storage = OverwriteStorage()

        for file_name in os.listdir(self.TMP_DIRECTORY):
            file_path = os.path.join(self.TMP_DIRECTORY, file_name)

            # Upload each file to Azure Storage
            with open(file_path, "rb") as f:
                storage.save_without_postfix(name=file_name, content=f)

            self.stdout.write(f"Successfully uploaded {file_name} to Azure Storage.")

    def remove_dump(self):
        """
        Remove the temporary directory and its contents.
        """
        shutil.rmtree(self.TMP_DIRECTORY)