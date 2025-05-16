from django import template

register = template.Library()


@register.filter(name="add_class")
def add_class(field, css_class):
    """Add CSS class to form field

    This template filter adds CSS classes to form fields, making it easy
    to apply tailwind/daisyUI styling to Django forms across the site.

    Example usage:
    {{ form.field|add_class:"input input-bordered w-full bg-white" }}
    """
    return field.as_widget(
        attrs={
            "class": f"{css_class} {field.field.widget.attrs.get('class', '')}",
        },
    )
