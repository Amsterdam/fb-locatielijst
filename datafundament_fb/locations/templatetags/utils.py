from django import template

register = template.Library()

@register.filter
def get_type(value):
    return type(value).__name__

@register.simple_tag
def set_query(request, field=None, value=None):
    """
    Return a url query based on the current url and optional added paramters
    Adjusted for ordering params
    """
    query = request.GET.copy()
    if query.get('order_by') == value:
        if query.get('order') == 'desc':
            query.pop('order', None)
        else:
            query['order'] = 'desc'
    else:
        if field:
            query.pop('order', None)
            query[field] = value
    return query.urlencode()
