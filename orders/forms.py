from django import forms
from .models import Order


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "given_name",
            "family_name",
            "email",
            "postal_address",
        ]
