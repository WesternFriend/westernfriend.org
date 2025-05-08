from django import template

register = template.Library()


@register.filter
def model_name(value):
    """Return the model name of the given object."""
    print(value)
    if value and hasattr(value, "_meta"):
        print(value._meta.model_name)
        return value._meta.model_name
    return ""
