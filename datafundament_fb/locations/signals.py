from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save, pre_delete
from locations.models import (
    PropertyGroup, LocationProperty, ExternalService, Location, LocationProperty, ExternalService, LocationData,
    LocationExternalService, PropertyOption)
from shared.utils import reorder_grouped_objects, add_log, get_log_object


@receiver(post_save, sender=PropertyGroup)
@receiver(post_save, sender=ExternalService)
@receiver(post_save, sender=LocationProperty)
def reorder_objects(sender, instance, raw, **kwargs):
    reorder_grouped_objects(sender, instance, raw, **kwargs)

@receiver(pre_save, sender=LocationData)
@receiver(pre_save, sender=LocationExternalService)
def location_data_change_log(sender, instance, raw, **kwargs):
    # Skip when importing fixtures
    if raw:
        return

    log_objects = get_log_object(instance)

    db_instance = sender.objects.get(id=instance.id) if instance.id else None
 
    for obj in log_objects:
        target = obj['target']
        value_name = obj['value_name']
        location = obj['location']

        instance_value = getattr(instance, value_name)

        if db_instance:
            current_value = getattr(db_instance, value_name, '')
            message = "Waarde was ({current_value}), is gewijzigd naar ({instance_value})"
        else:
            current_value = ''
            message = "Waarde ({instance_value}) gezet"
             
        if current_value != instance_value:
            message = message.format(current_value=current_value, instance_value=instance_value)
            add_log(location, instance.last_modified_by, target, message)

@receiver(pre_save, sender=ExternalService)
@receiver(pre_save, sender=PropertyOption)
@receiver(pre_save, sender=LocationProperty)
@receiver(pre_save, sender=Location)
def model_change_log(sender, instance, raw, **kwargs):
    # Skip when importing fixtures
    if raw:
        return
    target = instance # TODO HIER NOG WAT MEE DOEN? Bij locatie levert dit niet zo'n mooie registratie op

    if instance.id:
        log_objects = get_log_object(instance)
        db_instance = sender.objects.get(id=instance.id)

        for obj in log_objects:
            field = obj['target']
            value_name = obj['value_name']
            
            instance_value = getattr(instance, value_name)
            current_value = getattr(db_instance, value_name, '')
            message = "{field} was ({current_value}), is gewijzigd naar ({instance_value})"

            if current_value != instance_value:
                message = message.format(field=field, current_value=current_value, instance_value=instance_value)
                add_log(instance, instance.last_modified_by, target, message)
    else:
        message = f'{instance} is aangemaakt.'
        add_log(None, instance.last_modified_by, target, message)

@receiver(pre_delete, sender=LocationData)
def locationdata_delete_log(sender, instance, **kwargs):
    target = instance.location_property.label
    message = f"Waarde ({instance.value}) verwijderd"
    add_log(instance.location, instance.last_modified_by, target, message)

@receiver(pre_delete, sender=PropertyOption)
@receiver(pre_delete, sender=LocationProperty)
@receiver(pre_delete, sender=ExternalService)
def model_delete_log(sender, instance, **kwargs):
    target = instance
    message = f"Dit onderdeel is verwijderd"
    add_log(sender, instance.last_modified_by, target, message)
