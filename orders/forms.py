from typing import Any

from django import forms

from .models import Order


class OrderCreateForm(forms.ModelForm):
    # Autocomplete tokens let browsers and assistive tech identify
    # personal-data fields (WCAG 2.1 SC 1.3.5 Identify Input Purpose).
    AUTOCOMPLETE_TOKENS = {
        "purchaser_given_name": "given-name",
        "purchaser_family_name": "family-name",
        "purchaser_meeting_or_organization": "organization",
        "purchaser_email": "email",
        "recipient_name": "shipping name",
        "recipient_street_address": "shipping street-address",
        "recipient_postal_code": "shipping postal-code",
        "recipient_address_locality": "shipping address-level2",
        "recipient_address_region": "shipping address-level1",
        "recipient_address_country": "shipping country",
    }

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.fields["shipping_cost"].widget = forms.HiddenInput()

        for field_name, token in self.AUTOCOMPLETE_TOKENS.items():
            self.fields[field_name].widget.attrs["autocomplete"] = token

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
            "recipient_street_address": "Recipient street address and/or PO box number",
            "recipient_address_locality": "City",
            "recipient_address_region": "State",
            "recipient_address_country": "Country",
        }
