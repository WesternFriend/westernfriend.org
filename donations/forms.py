from django import forms

from .models import Donation

# TODO: Add "email" field and make it mandatory
class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = [
            "amount",
            "donor_email",
        ]
