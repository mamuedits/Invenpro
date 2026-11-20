from django import template
from decimal import Decimal

register = template.Library()


@register.simple_tag(takes_context=True)
def money(context, value):
    """
    Renders an amount (stored in Base INR) converted to the active currency with its symbol.
    Usage: {% money product.purchase_price %}
    """
    if value is None or value == '':
        value = Decimal('0.00')
    try:
        dec_val = Decimal(str(value))
    except Exception:
        dec_val = Decimal('0.00')

    request = context.get('request')
    profile = getattr(request.user, 'profile', None) if request and request.user.is_authenticated else None

    if profile:
        converted = profile.convert_from_base(dec_val)
        symbol = profile.currency_symbol
    else:
        converted = dec_val
        symbol = '₹'

    return f"{symbol}{converted:,.2f}"


@register.filter
def money_val(value, user):
    """
    Returns only the converted numeric value (without symbol) for JS or calculations.
    Usage: {{ product.stock_value|money_val:request.user }}
    """
    if value is None or value == '':
        return '0.00'
    try:
        dec_val = Decimal(str(value))
    except Exception:
        return '0.00'

    profile = getattr(user, 'profile', None) if user and user.is_authenticated else None
    if profile:
        converted = profile.convert_from_base(dec_val)
    else:
        converted = dec_val

    return f"{converted:.2f}"

