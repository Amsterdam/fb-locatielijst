from locations.models import Log

def reorder_grouped_objects(sender, instance, raw, **kwargs):
    """
    Function to re-index a bunch of instances on their order field when one instance has been altered on that field
    Usually triggered from a post_save signal
    """
    # Don't run when a fixture is loaded (=raw)
    if not raw:
        # Get order of the modified instance
        instance_order = getattr(instance, 'order', None)
        # Set index to 1
        index = 1

        # Get the model objects depending on the model
        match sender.__name__:
            case 'LocationProperty':
                objects = sender.objects.filter(group=instance.group).order_by('order')
            case _:
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

def add_log(location, user, target, message):
    Log.objects.create(location = location, user = user, target = target, message = message)
