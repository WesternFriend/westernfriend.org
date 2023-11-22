from django import forms
from django_registration.forms import RegistrationForm
from django_recaptcha.fields import ReCaptchaField
from accounts.models import User


class CustomUserForm(RegistrationForm):
    """Custom user registration form with captcha."""

    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    captcha = ReCaptchaField()

    class Meta(RegistrationForm.Meta):
        model = User
        fields = [
            User.USERNAME_FIELD,
            "first_name",
            "last_name",
            "password1",
            "password2",
        ]
