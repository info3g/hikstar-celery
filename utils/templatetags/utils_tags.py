from django import template

register = template.Library()


@register.filter
def split(value: str, split_by: str = "\r\n") -> list:
    """
    Splits value by the value of `split_by`
    """
    return value.split(split_by)
