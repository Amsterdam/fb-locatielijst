from django.dispatch import receiver
from django.db.models.signals import post_save
from locations.models import PropertyGroup, LocationProperty

@receiver(post_save, sender=PropertyGroup)
def reorder_property_groups(instance, **kwargs):
    # Get order of the modified instance
    instance_order = getattr(instance, 'order', None)

    # nodig om created te gebruiken? Heeft ook een nieuwe instance hier een id gekregen? Anders exclude gebruiken?
    objects = PropertyGroup.objects.all().order_by('order')
    index = 1
    for object in objects:
        # skip if the current object is the instance and order has been filled
        if object.id == instance.id and instance_order:
            continue

        # if index is the same as the instance.order, add 1 to the index
        if index == instance_order:
            index += 1

        # update the object with the index and add 1 for the next
        PropertyGroup.objects.filter(id=object.id).update(order=index)
        index += 1


@receiver(post_save, sender=LocationProperty)
def reorder_location_properties(instance, **kwargs):
    # Get order of the modified instance
    instance_order = getattr(instance, 'order', None)

    objects = LocationProperty.objects.filter(group=instance.group).order_by('order')
    index = 1
    for object in objects:
        # skip if the current object is the instance and order has been filled
        if object.id == instance.id and instance_order:
            continue

        # if index is the same as the instance.order, add 1 to the index
        if index == instance_order:
            index += 1

        # update the object with the index and add 1 for the next
        LocationProperty.objects.filter(id=object.id).update(order=index)
        index += 1    
