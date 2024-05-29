from django import template

register = template.Library()

@register.filter
def get_type(value):
    return type(value).__name__

@register.filter
def verbose_name(model, plural=False):
    if plural:
        return model._meta.verbose_name_plural
    return model._meta.verbose_name

@register.filter
def reverse_url(instance, view):
    return instance._meta.model_name + "-" + view