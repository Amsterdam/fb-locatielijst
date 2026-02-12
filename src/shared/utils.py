from django.contrib.contenttypes.models import ContentType

from locations.models import Log
from shared.context import current_user


def reorder_grouped_objects(sender, instance, raw, **kwargs):
    """
    Function to re-index a bunch of instances on their order field when one instance has been altered on that field
    Usually triggered from a post_save signal
    """
    # Don't run when a fixture is loaded (=raw)
    if not raw:
        # Get order of the modified instance
        instance_order = getattr(instance, "order", None)
        # Set index to 1
        index = 1

        # Get the model objects depending on the model
        match sender.__name__:
            case "LocationProperty":
                objects = sender.objects.filter(group=instance.group).order_by("order")
            case _:
                objects = sender.objects.all().order_by("order")

        for object in objects:
            # skip if the current object is the instance and order has been filled
            if object.id == instance.id and instance_order:
                continue

            # if index is the same as the instance.order, add 1; otherwise 2 object will have the same index
            if index == instance_order:
                index += 1

            # update the object with the index and add 1 for the next iteration
            sender.objects.filter(id=object.id).update(order=index)
            index += 1


def add_log(instance, action, field, message):
    """
    Write a log entry to the database
    """
    content_type = ContentType.objects.get_for_model(instance)
    user = current_user.get()
    Log.objects.create(
        user=user,
        content_type=content_type,
        action=action,
        object_name=str(instance),
        object_id=instance.id,
        field=field,
        message=message,
    )


def get_log_parameters(instance) -> list:
    """
    Return a list of dictionaries containing the field that is modified (attribute_name)
    and the name the field will have in the log field.
    The name of the field will default to the verbose_name of the model field,
    but if a tuple is given than the referenced object is used as a name
    """
    match instance.__class__.__name__:
        case "LocationData":
            parameters = [("value", instance.location_property.label)]
        case "LocationExternalService":
            parameters = [("external_location_code", instance.external_service.name)]
        case "Location":
            parameters = ["pandcode", "name", "is_archived"]
        case "LocationProperty":
            parameters = [
                "short_name",
                "label",
                "required",
                "multiple",
                "unique",
                "public",
            ]
        case "PropertyOption":
            parameters = ["option"]
        case "ExternalService":
            parameters = ["name", "short_name", "public"]

    log_parameters = []
    for param in parameters:
        if type(param) is tuple:
            attribute_name = param[0]
            display_name = param[1]
        else:
            attribute_name = param
            display_name = instance._meta.get_field(param).verbose_name
        log_parameters.append(
            {
                "attribute_name": attribute_name,
                "display_name": display_name,
            }
        )

    return log_parameters
