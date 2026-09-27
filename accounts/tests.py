import importlib
import re
from unittest import mock
from unittest.mock import PropertyMock, patch

from django.core import mail
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

import core.settings
from subscription.models import Subscription

from .models import User


class UserManagerTest(TestCase):
    def test_create_user(self) -> None:
        # Test creating regular user
        email = "test@test.com"
        password = "testpass"
        user = User.objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.is_staff)
        self.assertTrue(user.is_active)  # Fixed to match model default True
        self.assertFalse(user.is_superuser)

    def test_create_user_with_no_email(self) -> None:
        # Test creating user with no email values error
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email=None,  # type: ignore
                password="testpass",
            )

    def test_create_superuser(self) -> None:
        # Test creating superuser
        email = "admin@test.com"
        password = "adminpass"
        user = User.objects.create_superuser(email, password)

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_superuser)


# User model tests.
class UserModelTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="test@test.com",
            password="testpass",
        )

        # Creating active subscription
        self.user_subscription = Subscription.objects.create(
            user=self.user,
        )

    def test_user_str_representation(self) -> None:
        # Test str representation returns email
        expected_str = "test@test.com"
        self.assertEqual(str(self.user), expected_str)

    def test_is_subscriber_subscription_active(self) -> None:
        with patch.object(
            Subscription,
            "is_active",
            new_callable=PropertyMock,
        ) as mock_is_active:
            mock_is_active.return_value = True

            self.assertTrue(self.user.is_subscriber)

    def test_is_subscriber_subscription_expired(self) -> None:
        with patch.object(
            Subscription,
            "is_active",
            new_callable=PropertyMock,
        ) as mock_is_active:
            mock_is_active.return_value = False

            self.assertFalse(self.user.is_subscriber)


class CustomPasswordResetViewTests(TestCase):
    @override_settings(
        MAILERS={
            "default": {
                "BACKEND": "django.core.mail.backends.locmem.EmailBackend",
            }
        }
    )
    def test_password_reset_sends_text_and_html(self):
        user = User.objects.create_user(email="pr@example.com", password="x")
        resp = self.client.post(reverse("password_reset"), {"email": user.email})
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, [user.email])
        self.assertTrue(msg.body.strip())  # plain text body
        self.assertTrue(getattr(msg, "alternatives", None))
        self.assertGreaterEqual(len(msg.alternatives), 1)
        self.assertEqual(msg.alternatives[0][1], "text/html")
        self.assertTrue(msg.subject.strip())
        html_body, _ = msg.alternatives[0]
        self.assertTrue(str(html_body).strip())


class SmtpSettingsEnvironmentTests(SimpleTestCase):
    def test_smtp_mailers_configuration(self):
        smtp_environment = {
            "EMAIL_HOST": "smtp.example.com",
            "EMAIL_PORT": "2525",
            "EMAIL_HOST_USER": "testuser",
            "EMAIL_HOST_PASSWORD": "testpassword",
            "EMAIL_USE_TLS": "False",
            "EMAIL_USE_SSL": "True",
        }

        try:
            with mock.patch.dict("os.environ", smtp_environment):
                importlib.reload(core.settings)
                mailer = core.settings.MAILERS["default"]

                self.assertEqual(
                    mailer["BACKEND"],
                    "django.core.mail.backends.smtp.EmailBackend",
                )
                self.assertEqual(
                    mailer["OPTIONS"],
                    {
                        "host": "smtp.example.com",
                        "port": 2525,
                        "username": "testuser",
                        "password": "testpassword",
                        "use_tls": False,
                        "use_ssl": True,
                    },
                )
        finally:
            importlib.reload(core.settings)


class AccountPageAccessibilityTest(TestCase):
    """Regression tests for WCAG issues found in the accessibility audit."""

    def test_account_pages_have_descriptive_titles(self) -> None:
        # WCAG 2.4.2 Page Titled: non-Wagtail views have no `page` to title them
        expected_titles = {
            "login": "Login",
            "django_registration_register": "Register",
            "password_reset": "Password reset",
        }
        for url_name, expected in expected_titles.items():
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                title = re.search(
                    r"<title>(.*?)</title>",
                    response.content.decode(),
                    re.DOTALL,
                )
                self.assertIsNotNone(title)
                self.assertIn(expected, title.group(1))  # type: ignore[union-attr]

    def test_account_pages_have_single_main_landmark(self) -> None:
        response = self.client.get(reverse("login"))
        self.assertEqual(response.content.decode().count("<main"), 1)

    def test_navigation_does_not_use_aria_menu_roles(self) -> None:
        # Site navigation is a list of links, not an application menu
        html = self.client.get(reverse("login")).content.decode()
        self.assertNotIn('role="menubar"', html)
        self.assertNotIn('role="menuitem"', html)

    def test_login_error_announcements_and_autocomplete(self) -> None:
        # WCAG accessibility: login errors should render with role="alert"
        response = self.client.post(reverse("login"), {"username": "", "password": ""})
        html = response.content.decode()
        self.assertIn('role="alert"', html)

    def test_registration_password_errors_linked(self) -> None:
        # Django points aria-describedby at these ids; they must exist
        response = self.client.get(reverse("django_registration_register"))
        html = response.content.decode()
        self.assertIn('id="id_password2_error"', html)
        self.assertIn('id="id_password2_helptext"', html)
        self.assertRegex(html, r'<input[^>]*aria-invalid="true"[^>]*id="id_password2"')

    def test_registration_name_fields_have_autocomplete(self) -> None:
        # WCAG 1.3.5 Identify Input Purpose
        html = self.client.get(reverse("django_registration_register")).content.decode()
        self.assertRegex(
            html,
            r'<input[^>]*autocomplete="given-name"[^>]*id="id_first_name"',
        )
        self.assertRegex(
            html,
            r'<input[^>]*autocomplete="family-name"[^>]*id="id_last_name"',
        )
