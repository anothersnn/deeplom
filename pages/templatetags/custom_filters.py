from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    return value * arg

@register.filter
def to_int(value):
    return int(value) if value is not None else 0