from django import template
from django.utils import timezone
from django.utils.formats import date_format


register = template.Library()


def _localize(value):
    if not value:
        return value
    if timezone.is_aware(value):
        return timezone.localtime(value)
    return value


@register.filter
def friendly_time(value):
    value = _localize(value)
    if not value:
        return ''
    if value.hour == 12 and value.minute == 0:
        return 'Noon'
    if value.hour == 0 and value.minute == 0:
        return 'Midnight'
    return date_format(value, 'g:i A')


@register.filter
def friendly_datetime(value):
    value = _localize(value)
    if not value:
        return ''
    return f"{date_format(value, 'M d, Y')} {friendly_time(value)}"
