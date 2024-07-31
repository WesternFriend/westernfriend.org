from django import forms
from django_registration.forms import RegistrationForm
from accounts.models import User


class CustomUserForm(RegistrationForm):
    """Custom user registration form with captcha."""

    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta(RegistrationForm.Meta):
        model = User
        fields = [
            User.USERNAME_FIELD,
            "first_name",
            "last_name",
            "password1",
            "password2",
        ]
