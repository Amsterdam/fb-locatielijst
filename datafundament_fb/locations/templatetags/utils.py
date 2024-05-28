from django import template

register = template.Library()

@register.filter
def get_type(value):
    return type(value).__name__

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
        if query.get('order_by') == value:
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
def get_order(request, value=None):
    """
    Return if the value is in de 'order_by' paramenter of the url.
    If so, return the order direction (asc/desc)
    If not, result ''
    """
    order_by = request.GET.get('order_by')
    order = request.GET.get('order')
    # Only check the parameter if present 
    if order_by:
        # Compare parameter with the value
        if order_by == value:
            # Get the default order direction
            if order == 'desc':
                return 'desc'
            else:
                return 'asc'
        else:
            return ''

    return ''
