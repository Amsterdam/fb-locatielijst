from django import template

register = template.Library()

@register.filter
def get_type(value):
    return type(value).__name__

@register.simple_tag
def set_query(request, parameter=None, value=None):
    """
    Return a url query based on the current url and optional added paramters
    Adjusted for ordering params
    """
    query = request.GET.copy()
    # Only alter the query if a query parameter is present 
    if parameter:
        if query.get('order_by') == value:
            if query.get('order') == 'desc':
                query.pop('order', None)
            else:
                query['order'] = 'desc'
        else:
            query.pop('order', None)
            query[parameter] = value
    return query.urlencode()
