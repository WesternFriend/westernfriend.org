from django import forms

from .models import Donation, DonorAddress


class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = [
            "amount",
            "donor_given_name",
            "donor_family_name",
            "donor_email",
        ]


class DonorAddressForm(forms.ModelForm):
    class Meta:
        model = DonorAddress
        exclude = ["address_type", "latitude", "longitude", "po_box_number"]
