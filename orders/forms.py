from django import forms
from .models import Order


class OrderCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(OrderCreateForm, self).__init__(*args, **kwargs)
        self.fields["shipping_cost"].widget = forms.HiddenInput()

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
            "shipping_cost",
        ]

        labels = {
            "address_locality": "City",
            "address_region": "State",
            "address_country": "Country",
        }
