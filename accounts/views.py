from typing import Any
from django.conf import settings
from django.utils.decorators import method_decorator
from django.contrib import messages

from django_registration.backends.activation.views import RegistrationView  # type: ignore
from honeypot.decorators import check_honeypot  # type: ignore

from accounts.forms import CustomUserForm
from django.contrib.auth.views import PasswordResetView, LoginView
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse, NoReverseMatch
from urllib.parse import urlparse


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


class CustomPasswordResetView(PasswordResetView):
    """Send both plain text and HTML password reset emails.

    - `email_template_name` is the plain-text body.
    - `html_email_template_name` is the HTML alternative.
    """

    subject_template_name = "registration/password_reset_subject.txt"
    email_template_name = "registration/password_reset_email.txt"
    html_email_template_name = "registration/password_reset_email.html"


class CustomLoginView(LoginView):
    """Use site login template and sanitize unsafe or admin `next` redirects.

    Prevents redirecting non-admin users to the admin interface which
    would result in a forbidden/permission error after login.
    """

    template_name = "registration/login.html"

    def get_success_url(self):
        request = self.request
        redirect_to = self.get_redirect_url()

        # Fallback to settings.LOGIN_REDIRECT_URL if no valid next.
        if not redirect_to:
            return super().get_success_url()

        parsed = urlparse(redirect_to)
        is_absolute = bool(parsed.netloc)

        # Ensure the redirect target is allowed for this host.
        if not url_has_allowed_host_and_scheme(
            redirect_to,
            allowed_hosts={request.get_host()},
        ):
            return super().get_success_url()

        # If absolute URL and current request is secure, only allow https scheme
        if is_absolute and request.is_secure() and parsed.scheme != "https":
            return super().get_success_url()

        # Determine canonical admin paths to avoid redirecting users there
        try:
            wagtail_admin_home = reverse("wagtailadmin_home")
        except NoReverseMatch:
            wagtail_admin_home = "/admin/"

        admin_base_setting = getattr(settings, "WAGTAILADMIN_BASE_URL", "/admin")
        admin_base_path = urlparse(admin_base_setting).path or admin_base_setting

        def normalize(p: str) -> str:
            return p if p.startswith("/") else f"/{p}"

        def is_under(path: str, base: str) -> bool:
            base = base.rstrip("/")
            return path == base or path.startswith(base + "/")

        redirect_path = parsed.path or redirect_to
        redirect_path = normalize(redirect_path)

        if any(
            is_under(redirect_path, normalize(p))
            for p in (wagtail_admin_home, admin_base_path)
        ):
            # Avoid redirecting users into the admin; use default redirect
            return self.get_default_redirect_url()

        return redirect_to
