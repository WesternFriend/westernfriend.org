from django import template

register = template.Library()


@register.filter
def model_name(value):
    """Return the model name of the given object."""

    if value and hasattr(value, "_meta"):
        return value._meta.model_name
    return ""
