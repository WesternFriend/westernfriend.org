from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import Subscription


class SubscriptionCreateForm(forms.ModelForm):

    class Meta:
        model = Subscription
        fields = [
            "subscription_type",
            "duration",
            "subscriber_given_name",
            "subscriber_family_name",
            "subscriber_email",
            "subscriber_street_address",
            "subscriber_po_box_number",
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


class UserRegisterationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'password1', 'password2', )