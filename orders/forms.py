from django import forms
from .models import Order


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "given_name",
            "family_name",
            "email",
            "street_address",
            "po_box_number",
            "postal_code",
            "address_locality",
            "address_region",
            "address_country",
        ]
