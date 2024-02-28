from django.dispatch import receiver
from django.db.models.signals import post_save
from help_docs.models import Documentation


@receiver(post_save, sender=Documentation)
def reorder_objects(sender, instance, raw, **kwargs):
    # Don't run when a fixture is loaded (=raw)
    if not raw:
        # Get order of the modified instance
        instance_order = getattr(instance, 'order', None)
        # Set index to 1
        index = 1

        # Get the model objects
        objects = sender.objects.all().order_by('order')

        for object in objects:
            # skip if the current object is the instance and order has been filled
            if object.id == instance.id and instance_order:
                continue

            # if index is the same as the instance.order, add 1 to the index; otherwise 2 object will have the same index
            if index == instance_order:
                index += 1

            # update the object with the index and add 1 for the next iteration
            sender.objects.filter(id=object.id).update(order=index)
            index += 1    

