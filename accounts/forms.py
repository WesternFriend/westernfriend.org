from django_registration.forms import RegistrationForm
from django_recaptcha.fields import ReCaptchaField
from accounts.models import User


class CustomUserForm(RegistrationForm):
    """Custom user registration form with captcha."""

    captcha = ReCaptchaField()

    class Meta(RegistrationForm.Meta):
        model = User
