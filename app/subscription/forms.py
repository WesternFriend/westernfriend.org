from django import forms

from .models import Subscription


class SubscriptionCreateForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = [
            "format",
            "price_group",
            "recurring",
            "subscriber_given_name",
            "subscriber_family_name",
            "subscriber_street_address",
            "subscriber_street_address_line_2",
            "subscriber_postal_code",
            "subscriber_address_locality",
            "subscriber_address_region",
            "subscriber_address_country",
        ]

        labels = {
            "subscriber_address_locality": "City",
            "subscriber_address_region": "State",
            "subscriber_address_country": "Country",
        }
