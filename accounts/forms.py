from django import forms
from django_registration.forms import RegistrationForm
from wagtail.users.forms import UserCreationForm, UserEditForm

from accounts.models import User


class CustomUserForm(RegistrationForm):
    """Custom user registration form with captcha."""

    # Autocomplete tokens satisfy WCAG 2.1 SC 1.3.5 (Identify Input Purpose)
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={"autocomplete": "given-name"}),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={"autocomplete": "family-name"}),
    )

    class Meta(RegistrationForm.Meta):
        model = User
        fields = [
            User.USERNAME_FIELD,
            "first_name",
            "last_name",
            "password1",
            "password2",
        ]


class CustomUserEditForm(UserEditForm):
    """Custom user edit form with first and last name fields."""

    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta(UserEditForm.Meta):
        model = User
        fields = [
            User.USERNAME_FIELD,
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "is_superuser",
        ]


class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form with first and last name fields."""

    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = [
            User.USERNAME_FIELD,
            "first_name",
            "last_name",
            "password1",
            "password2",
            "is_active",
            "is_staff",
            "is_superuser",
        ]
