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
    return "locations_urls:" + instance._meta.model_name + "-" + view

@register.simple_tag
def set_query(request, parameter=None, value=None, pop=False):
    """
    Return a url query based on the current url and optional added paramters
    Adjusted for ordering params
    """
    query = request.GET.copy()
    # Only alter the query if a query parameter is present 
    if parameter:
        # Add order and direction to query
        if query.get('order_by') == value or (query.get('order_by') is None and value == 'pandcode'):
        # Set default order direction
            if query.get('order') == 'desc':
                query.pop('order', None)
            else:
                query['order'] = 'desc'
        else:
            query.pop('order', None)

            # Add or remove the parameter to the query
            if pop:
                query.pop(parameter, None)
            else:
                query[parameter] = value

    return query.urlencode()

@register.simple_tag
def get_order(request, column=None):
    """
    Return asc/desc if the column name is in de 'order_by' paramenter of the url.
    When no order_by parameter is present but column name is pandcode, default to ascending for name column
    """
    order_by = request.GET.get('order_by')
    order = request.GET.get('order')
    # Set order for the requested column
    if order_by == column:
        if order == 'desc':
            value = 'desc'
        else:
            value = 'asc'
    # Set order when column is pandcode
    elif column == 'name' and not order_by:
        if order == 'desc':
            value = 'desc'
        else:
            value = 'asc'
    else:
        value = ''
    return value
