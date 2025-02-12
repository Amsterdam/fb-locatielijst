from django.dispatch import receiver
from django.db.models.signals import post_save
from help_docs.models import Documentation
from shared import utils

@receiver(post_save, sender=Documentation)
def reorder_objects(sender, instance, raw, **kwargs):
    utils.reorder_grouped_objects(sender, instance, raw, **kwargs)

