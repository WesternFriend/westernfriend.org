from typing import Any
from django.conf import settings
from django.utils.decorators import method_decorator
from django.contrib import messages

from django_registration.backends.activation.views import RegistrationView  # type: ignore
from honeypot.decorators import check_honeypot  # type: ignore

from accounts.forms import CustomUserForm


@method_decorator(check_honeypot, name="post")
class CustomRegistrationView(RegistrationView):
    form_class = CustomUserForm
    success_url = "/"
    template_name = "django_registration/registration_form.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add honeypot field to context."""
        context = super().get_context_data(**kwargs)

        context["honeypot_field_name"] = settings.HONEYPOT_FIELD_NAME

        return context

    def form_valid(self, form):
        check_email_message = """Thanks for starting to register an account on our website.
        To complete your registration, please check your email for an message from us.
        You should have just received one. Please look in your spam / junk folder if our message is not in your inbox"""
        # notice we use `self.request` here since the request is a member of the CustomRegistrationView instance
        messages.info(self.request, check_email_message)

        return super().form_valid(form)
