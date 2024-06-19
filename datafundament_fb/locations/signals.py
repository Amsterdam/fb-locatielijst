from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save, pre_delete
from locations.models import (
    PropertyGroup, LocationProperty, ExternalService, Location, LocationProperty, ExternalService, LocationData,
    LocationExternalService, PropertyOption)
from shared.utils import reorder_grouped_objects, add_log, get_log_parameters

@receiver(post_save, sender=PropertyGroup)
@receiver(post_save, sender=ExternalService)
@receiver(post_save, sender=LocationProperty)
def reorder_objects(sender, instance, raw, **kwargs):
    reorder_grouped_objects(sender, instance, raw, **kwargs)

@receiver(post_save, sender=LocationData)
@receiver(post_save, sender=LocationExternalService)
def property_create_log(instance, raw, created, **kwargs):
    """
    Create a log whenever the value of a location property is added
    """
    if created:
        for param in get_log_parameters(instance):
            action = 2
            field = param['display_name']
            instance_value = getattr(instance, param['attribute_name'])

            # Only create a log when the property has location data
            if instance_value:
                message = f"Waarde ({instance_value}) gezet."
                add_log(instance.location, action, field, message)

@receiver(pre_save, sender=LocationData)
@receiver(pre_save, sender=LocationExternalService)
def property_change_log(sender, instance, raw, **kwargs):
    """
    Create a log whenever the value of a location property changes
    """
    if instance.id and not raw:
        db_instance = sender.objects.filter(id=instance.id).first()
        for param in get_log_parameters(instance):
            action = 2
            field = param['display_name']
            attribute_name = param['attribute_name']
            instance_value = getattr(instance, attribute_name)
            current_value = getattr(db_instance, attribute_name, '')

            if current_value != instance_value:
                message = f"Waarde was ({current_value}), is gewijzigd naar ({instance_value})."
                add_log(instance.location, action, field, message)

@receiver(pre_delete, sender=LocationData)
def property_delete_log(instance, **kwargs):
    """
    When a location property of the type 'multiple' is deleted a log entry is added as a location change
    """
    action = 2
    field = instance.location_property.label
    message = f"Waarde ({instance.value}) verwijderd."
    add_log(instance.location, action, field, message)

@receiver(post_save, sender=ExternalService)
@receiver(post_save, sender=PropertyOption)
@receiver(post_save, sender=LocationProperty)
@receiver(post_save, sender=Location)
def model_create_log(instance, raw, created, **kwargs):
    """
    Create a log event whenever an instance of one of these models is added 
    """
    if created:
        action = 0
        field = instance._meta.verbose_name
        message = f'{instance} is aangemaakt.'
        add_log(instance, action, field, message)

@receiver(pre_save, sender=ExternalService)
@receiver(pre_save, sender=PropertyOption)
@receiver(pre_save, sender=LocationProperty)
@receiver(pre_save, sender=Location)
def model_change_log(sender, instance, raw, **kwargs):
    """
    Create a log event whenever an instance of one of these models is modified 
    """
    if instance.id and not raw:
        db_instance = sender.objects.filter(id=instance.id).first()
        for param in get_log_parameters(instance):
            action = 2
            field = param['display_name']
            attribute_name = param['attribute_name']
            instance_value = getattr(instance, attribute_name)
            current_value = getattr(db_instance, attribute_name, '')

            if current_value != instance_value:
                message = f"Waarde was ({current_value}), is gewijzigd naar ({instance_value})."
                add_log(instance, action, field, message)

@receiver(pre_delete, sender=Location)
@receiver(pre_delete, sender=PropertyOption)
@receiver(pre_delete, sender=LocationProperty)
@receiver(pre_delete, sender=ExternalService)
def model_delete_log(instance, **kwargs):
    """
    Whenever an instance of one of the above models is deleted a log event is created 
    """
    action = 3
    field = None
    message = f"{instance} is verwijderd."
    add_log(instance, action, field, message)

def disconnect_signals():
    """
    Use when signals need to be disabled temporarily, for instance during unit tests
    """
    post_save.disconnect(property_create_log, sender=LocationData)
    post_save.disconnect(property_create_log, sender=LocationExternalService)
    pre_save.disconnect(property_change_log, sender=LocationData)
    pre_save.disconnect(property_change_log, sender=LocationExternalService)
    pre_delete.disconnect(property_delete_log, sender=LocationData)
    
    post_save.disconnect(model_create_log, sender=Location)
    post_save.disconnect(model_create_log, sender=LocationProperty)
    post_save.disconnect(model_create_log, sender=PropertyOption)
    post_save.disconnect(model_create_log, sender=ExternalService)
    pre_save.disconnect(model_change_log, sender=Location)
    pre_save.disconnect(model_change_log, sender=LocationProperty)
    pre_save.disconnect(model_change_log, sender=PropertyOption)
    pre_save.disconnect(model_change_log, sender=ExternalService)
    pre_delete.disconnect(model_delete_log, sender=Location)
    pre_delete.disconnect(model_delete_log, sender=LocationProperty)
    pre_delete.disconnect(model_delete_log, sender=PropertyOption)
    pre_delete.disconnect(model_delete_log, sender=ExternalService)

def connect_signals():
    """
    Use when signals need to be connected, after disabling, for instance during unit tests
    """
    post_save.connect(property_create_log, sender=LocationData)
    post_save.connect(property_create_log, sender=LocationExternalService)
    pre_save.connect(property_change_log, sender=LocationData)
    pre_save.connect(property_change_log, sender=LocationExternalService)
    pre_delete.connect(property_delete_log, sender=LocationData)
    
    post_save.connect(model_create_log, sender=Location)
    post_save.connect(model_create_log, sender=LocationProperty)
    post_save.connect(model_create_log, sender=PropertyOption)
    post_save.connect(model_create_log, sender=ExternalService)
    pre_save.connect(model_change_log, sender=Location)
    pre_save.connect(model_change_log, sender=LocationProperty)
    pre_save.connect(model_change_log, sender=PropertyOption)
    pre_save.connect(model_change_log, sender=ExternalService)
    pre_delete.connect(model_delete_log, sender=Location)
    pre_delete.connect(model_delete_log, sender=LocationProperty)
    pre_delete.connect(model_delete_log, sender=PropertyOption)
    pre_delete.connect(model_delete_log, sender=ExternalService)

