from typing import Any
from django import forms

from .models import Order


class OrderCreateForm(forms.ModelForm):
    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.fields["shipping_cost"].widget = forms.HiddenInput()

    class Meta:
        model = Order
        fields = [
            "purchaser_given_name",
            "purchaser_family_name",
            "purchaser_meeting_or_organization",
            "purchaser_email",
            "recipient_name",
            "recipient_street_address",
            "recipient_postal_code",
            "recipient_address_locality",
            "recipient_address_region",
            "recipient_address_country",
            "shipping_cost",
        ]

        labels = {
            "recipient_street_address": "Reicipient street address and/or PO box number",
            "recipient_address_locality": "City",
            "recipient_address_region": "State",
            "recipient_address_country": "Country",
        }
