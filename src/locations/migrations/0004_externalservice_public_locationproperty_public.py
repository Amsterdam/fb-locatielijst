# Generated by Django 5.0.1 on 2024-01-23 09:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("locations", "0003_alter_locationexternalservice_external_location_code"),
    ]

    operations = [
        migrations.AddField(
            model_name="externalservice",
            name="public",
            field=models.BooleanField(default=False, verbose_name="Zichtbaar voor niet ingelogde gebruikers"),
        ),
        migrations.AddField(
            model_name="locationproperty",
            name="public",
            field=models.BooleanField(default=False, verbose_name="Zichtbaar voor niet ingelogde gebruikers"),
        ),
    ]
