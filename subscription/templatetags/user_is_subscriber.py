import datetime

from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def user_is_subscriber(context):
    user = context["request"].user

    if hasattr(user, "subscriptions"):
        active_subscription = user.subscriptions.filter(
            end_date__gte=datetime.datetime.now(),
            paid=True
        )

        if active_subscription:
            return True
    
    return False