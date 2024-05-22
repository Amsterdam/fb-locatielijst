from django import template

register = template.Library()

@register.filter
def get_type(value):
    return type(value).__name__

@register.filter
def verbose_name(value, plural=None):
    if plural == 'plural':
        return value._meta.verbose_name_plural
    return value._meta.verbose_name

@register.filter
def reverse_url(value, view):
    return value._meta.model_name + "-" + view