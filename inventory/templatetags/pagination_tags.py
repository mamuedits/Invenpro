from django import template

register = template.Library()


@register.simple_tag
def get_elided_pages(page_obj, on_each_side=2, on_ends=1):
    """
    Returns an elided page range list (e.g. [1, '…', 12, 13, 14, 15, 16, '…', 50])
    so pagination NEVER overflows regardless of total page count.
    """
    if not page_obj or not hasattr(page_obj, 'paginator'):
        return []
    paginator = page_obj.paginator
    raw_range = paginator.get_elided_page_range(
        number=page_obj.number,
        on_each_side=on_each_side,
        on_ends=on_ends,
    )
    ellipsis = paginator.ELLIPSIS
    return [
        {'value': item, 'is_ellipsis': (item == ellipsis)}
        for item in raw_range
    ]


@register.simple_tag(takes_context=True)
def page_url(context, page_number):
    """
    Builds a query string preserving all current GET parameters (search, filters, dates)
    while setting ?page=<page_number>.
    """
    request = context.get('request')
    if not request:
        return f"?page={page_number}"
    params = request.GET.copy()
    params['page'] = page_number
    return f"?{params.urlencode()}"


@register.simple_tag(takes_context=True)
def non_page_query_items(context):
    """
    Returns all GET query items except 'page' so the 'Go to page' form keeps active filters.
    """
    request = context.get('request')
    if not request:
        return []
    items = []
    for key, values in request.GET.lists():
        if key == 'page':
            continue
        for val in values:
            items.append((key, val))
    return items
