from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def inr(value):
    """Format a database amount with Indian digit grouping and two paise digits."""
    try:
        amount = Decimal(str(value)).quantize(Decimal('0.01'))
    except (InvalidOperation, TypeError, ValueError):
        amount = Decimal('0.00')

    sign = '-' if amount < 0 else ''
    whole, fraction = f'{abs(amount):.2f}'.split('.')
    if len(whole) > 3:
        last_three = whole[-3:]
        remaining = whole[:-3]
        groups = []
        while remaining:
            groups.append(remaining[-2:])
            remaining = remaining[:-2]
        whole = ','.join(reversed(groups)) + ',' + last_three
    return f'{sign}₹{whole}.{fraction}'
