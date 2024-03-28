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

def add_log(model, user, target, message):
    """
    Write a log entry to the database
    """
    Log.objects.create(model=model, user=user, target=target, message=message)

def get_log_object(instance)-> list:
    """
    Return a list of dictionaries containing the field that is modified and the name of that field.
    The name of the field will default to the verbose_name of the model field,
    but if a tuple is given than the referenced object is used as a name 
    """
    match instance.__class__.__name__:
        case 'LocationData':
            location = instance.location
            target_object = [('value', instance.location_property.label)]
        case 'LocationExternalService':
            location = instance.location
            target_object = [('external_location_code', instance.external_service.name)]
        case 'Location':
            location = instance
            target_object = ['name', 'is_archived']
        case 'LocationProperty':
            location = None
            target_object = ['short_name', 'label', 'required', 'multiple', 'unique', 'public',]
        case 'PropertyOption':
            location = None
            target_object = ['option']
        case 'ExternalService':
            location  = None
            target_object = ['name', 'short_name', 'public']

    log_objects = []
    for obj in target_object:
        if type(obj) is tuple:
            attribute_name = obj[0]
            target = obj[1]
        else:
            attribute_name = obj
            target = instance._meta.get_field(obj).verbose_name
        log_objects.append({
            'value_name': attribute_name,
            'target': target,
            'location': location,
        })

    return log_objects