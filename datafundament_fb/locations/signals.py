from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save, pre_delete
from locations.models import (
    PropertyGroup, LocationProperty, ExternalService, Location, LocationProperty, ExternalService, LocationData,
    LocationExternalService)
from shared.utils import reorder_grouped_objects, add_log


@receiver(post_save, sender=PropertyGroup)
@receiver(post_save, sender=ExternalService)
@receiver(post_save, sender=LocationProperty)
def reorder_objects(sender, instance, raw, **kwargs):
    reorder_grouped_objects(sender, instance, raw, **kwargs)


#@receiver(pre_save, sender=Location)
#@receiver(pre_save, sender=LocationProperty)
#@receiver(pre_save, sender=ExternalService)
@receiver(pre_save, sender=LocationData)
@receiver(pre_save, sender=LocationExternalService)
def property_change_log(sender, instance, raw, **kwargs):
    # Skip when importing fixtures
    if raw:
        return
    
    match sender.__name__:
        case 'LocationData':
            target = instance.location_property.label
            value_name = 'value'
        case 'LocationExternalService':
            target = instance.external_service.name
            value_name = 'external_location_code'

    instance_value = getattr(instance, value_name)

    # Check if existing instance
    if instance.id:
        db_instance = sender.objects.get(id=instance.id)
        current_value = getattr(db_instance, value_name, '')
        message = "Waarde was {current_value}, is gewijzigd naar {instance_value}"
    else:
        current_value = ''
        message = "Waarde {instance_value} gezet"

    # naam, archief voor locatie
    if current_value != instance_value:
        message = message.format(current_value=current_value, instance_value=instance_value)
        add_log(instance.location, instance.last_modified_by, target, message)


@receiver(pre_save, sender=Location)
def location_change_log(sender, instance, raw, **kwargs):
    # Skip when importing fixtures
    if raw:
        return

    if instance.id:
        db_instance = sender.objects.get(id=instance.id)
        
        if db_instance.name != instance.name:
            target = instance._meta.get_field('name').verbose_name
            message = f"Waarde was {db_instance.name}, is gewijzigd naar {instance.name}"
            add_log(instance, instance.last_modified_by, target, message)
        if db_instance.is_archived != instance.is_archived:
            target = instance._meta.get_field('is_archived').verbose_name
            if instance.is_archived:
                message = f"Locatie is gearchiveerd"
            else:
                message = f"Locatie is gedearchiveerd"
            add_log(instance, instance.last_modified_by, target, message)
    else:
        target =  "Locatie"
        message = '{name} is aangemaakt'.format(name=instance.name)
        add_log(None, instance.last_modified_by, target, message)

# AANZETTEN WANNEER LOCATION_DATA UPDATE GEREGELD IS
# @receiver(pre_delete, sender=LocationData)
# def locationdata_delete_log(sender, instance, **kwargs):
#     target = instance.location_property.label
#     message = f"Waarde {instance.value} verwijderd"
#     add_log(instance.location, instance.last_modified_by, target, message)

# locatie eigenschappen, externe service toevoegen, opties: aanmken, verwijderen, aanpassen -> applicatielog
    