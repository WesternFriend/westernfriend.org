from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Subscription

UserModel = get_user_model()

class SubscriptionCreateForm(forms.ModelForm):

    class Meta:
        model = Subscription
        fields = [
            "subscription_type",
            "duration",
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


class UserRegisterationForm(UserCreationForm):
    class Meta:
        model = UserModel
        fields = ('email', 'password1', 'password2', )