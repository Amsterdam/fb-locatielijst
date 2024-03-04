from django.dispatch import receiver
from django.db.models.signals import post_save
from locations.models import PropertyGroup, LocationProperty, ExternalService
from shared import utils


@receiver(post_save, sender=PropertyGroup)
@receiver(post_save, sender=ExternalService)
@receiver(post_save, sender=LocationProperty)
def reorder_objects(sender, instance, raw, **kwargs):
    utils.reorder_objects(sender, instance, raw, **kwargs)

