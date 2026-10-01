import importlib
import re
import sys
from unittest import mock
from unittest.mock import PropertyMock, patch

from django.conf import Settings, settings
from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import resolve_url
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import NoReverseMatch, reverse

import core.settings
from accounts.views import CustomLoginView
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
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_superuser)

    def test_create_user_with_no_email(self) -> None:
        # Test creating user with no email raises error
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email=None,  # type: ignore
                password="testpass",
            )

    def test_create_superuser(self) -> None:
        # Test creating superuser
        email = "admin@test.com"
        password = "adminpass"
        user = User.objects.create_superuser(email=email, password=password)

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_superuser)


# User model tests
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

    def test_is_subscriber_subscription_active(self):
        with patch.object(
            Subscription,
            "is_active",
            new_callable=PropertyMock,
        ) as mock_is_active:
            mock_is_active.return_value = True

            self.assertTrue(self.user.is_subscriber)

    def test_is_subscriber_subscription_expired(self):
        with patch.object(
            Subscription,
            "is_active",
            new_callable=PropertyMock,
        ) as mock_is_active:
            mock_is_active.return_value = False

            self.assertFalse(self.user.is_subscriber)

    def test_user_without_subscription_is_not_subscriber(self) -> None:
        # Test if is_subscriber returns False if user has no subscription
        self.user.subscription.delete()

        # Reload the user object to make sure it reflects the recent changes
        self.user.refresh_from_db()

        self.assertFalse(self.user.is_subscriber)


class CustomLoginViewTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()

    def _call_get_success_url(self, next_value: str, *, secure: bool = False):
        request = self.factory.get(
            "/accounts/login/",
            {"next": next_value},
            secure=secure,
        )
        view = CustomLoginView()
        view.setup(request)
        return view.get_success_url()

    def test_fallback_when_reverse_missing_and_next_is_admin(self):
        # Patch accounts.views.reverse to raise NoReverseMatch to trigger fallback
        with patch("accounts.views.reverse", side_effect=NoReverseMatch()):
            url = self._call_get_success_url("/admin/")
        # Should fall back to LOGIN_REDIRECT_URL (resolve if it's a name)
        self.assertEqual(url, resolve_url(settings.LOGIN_REDIRECT_URL))

    def test_redirect_allows_safe_non_admin_next_when_reverse_missing(self):
        with patch("accounts.views.reverse", side_effect=NoReverseMatch()):
            url = self._call_get_success_url("/some-safe-page/")
        self.assertEqual(url, "/some-safe-page/")

    def test_fallback_when_next_absolute_to_other_host(self):
        # Absolute URL to a different host should be rejected
        url = self._call_get_success_url("https://example.com/elsewhere/")
        self.assertEqual(url, resolve_url(settings.LOGIN_REDIRECT_URL))

    def test_fallback_when_secure_request_and_next_http_same_host(self):
        # When request is secure, an absolute HTTP URL to same host should fallback
        url = self._call_get_success_url("http://testserver/unsafe-http/", secure=True)
        self.assertEqual(url, resolve_url(settings.LOGIN_REDIRECT_URL))

    @override_settings(WAGTAILADMIN_BASE_URL="/cms")
    def test_fallback_when_next_under_custom_admin_base(self):
        url = self._call_get_success_url("/cms/section/")
        self.assertEqual(url, resolve_url(settings.LOGIN_REDIRECT_URL))

    def test_allows_https_when_secure_request_and_next_https_same_host(self):
        url = self._call_get_success_url("https://testserver/safe/", secure=True)
        self.assertEqual(url, "https://testserver/safe/")

    def test_fallback_when_relative_admin_without_slash(self):
        url = self._call_get_success_url("admin")
        self.assertEqual(url, resolve_url(settings.LOGIN_REDIRECT_URL))

    def test_fallback_when_no_next(self):
        request = self.factory.get("/accounts/login/")
        view = CustomLoginView()
        view.setup(request)
        self.assertEqual(
            view.get_success_url(),
            resolve_url(settings.LOGIN_REDIRECT_URL),
        )

    def test_fallback_when_reverse_returns_custom_admin_path(self):
        with patch("accounts.views.reverse", return_value="/dashboard"):
            url = self._call_get_success_url("/dashboard/stats")
        self.assertEqual(url, resolve_url(settings.LOGIN_REDIRECT_URL))


class CustomPasswordResetViewTests(TestCase):
    @override_settings(
        MAILERS={
            "default": {
                "BACKEND": "django.core.mail.backends.locmem.EmailBackend",
            },
        },
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
        html_body, _html_mime = msg.alternatives[0]
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


class SecretKeySettingsTests(SimpleTestCase):
    """A missing SECRET_KEY must stop the process, not be invented per worker.

    The old fallback generated a random key, so each gunicorn worker ran with a
    different one: sessions and CSRF tokens signed by one were rejected by the
    others, and the real problem never surfaced.
    """

    def _reload_with(self, environment):
        with (
            mock.patch("dotenv.load_dotenv"),
            mock.patch.dict("os.environ", environment, clear=True),
        ):
            importlib.reload(core.settings)

    def tearDown(self):
        importlib.reload(core.settings)

    def test_refuses_to_start_without_a_key_in_production(self):
        with self.assertRaises(ImproperlyConfigured) as caught:
            self._reload_with({"DJANGO_DEBUG": "false"})

        # The message has to say which variable and how to make one, or the
        # person hitting it at 3am learns nothing from the crash.
        self.assertIn("DJANGO_SECRET_KEY", str(caught.exception))
        self.assertIn("get_random_secret_key", str(caught.exception))

    def test_refuses_an_empty_key_in_production(self):
        """An unset variable in a .env or compose file still defines it as ""."""
        with self.assertRaises(ImproperlyConfigured):
            self._reload_with({"DJANGO_DEBUG": "false", "DJANGO_SECRET_KEY": ""})

    def test_refuses_a_whitespace_only_key_in_production(self):
        """Whitespace is truthy, so a bare falsiness check would let it through.

        A key of spaces signs just as badly as no key at all.
        """
        with self.assertRaises(ImproperlyConfigured):
            self._reload_with({"DJANGO_DEBUG": "false", "DJANGO_SECRET_KEY": "   "})

    def test_surrounding_whitespace_is_stripped(self):
        """A trailing newline from a secrets file must not change the key."""
        self._reload_with(
            {"DJANGO_DEBUG": "false", "DJANGO_SECRET_KEY": "  a-real-secret\n"},
        )

        self.assertEqual(core.settings.SECRET_KEY, "a-real-secret")

    def test_uses_the_key_from_the_environment_in_production(self):
        self._reload_with(
            {"DJANGO_DEBUG": "false", "DJANGO_SECRET_KEY": "a-real-secret"},
        )

        self.assertEqual(core.settings.SECRET_KEY, "a-real-secret")

    def test_debug_still_runs_without_a_key(self):
        """Local development must not need a secret configured."""
        self._reload_with({"DJANGO_DEBUG": "true"})

        self.assertTrue(core.settings.SECRET_KEY)

    def test_collectstatic_runs_without_a_key(self):
        """The build runs collectstatic before the runtime secret exists.

        It signs nothing, so it gets a placeholder rather than a hard stop —
        the same exemption DATABASES already makes for this command.
        """
        with mock.patch.object(sys, "argv", ["manage.py", "collectstatic"]):
            self._reload_with({"DJANGO_DEBUG": "false"})

        self.assertTrue(core.settings.SECRET_KEY)

    def test_other_commands_still_fail_without_a_key(self):
        """The collectstatic exemption must not leak to anything that serves."""
        with mock.patch.object(sys, "argv", ["manage.py", "migrate"]):
            with self.assertRaises(ImproperlyConfigured):
                self._reload_with({"DJANGO_DEBUG": "false"})

    def test_fallback_keys_are_parsed_for_rotation(self):
        """Old keys keep existing sessions valid while a new key rolls out."""
        self._reload_with(
            {
                "DJANGO_DEBUG": "false",
                "DJANGO_SECRET_KEY": "new-key",
                "DJANGO_SECRET_KEY_FALLBACKS": " old-key , older-key ,",
            },
        )

        self.assertEqual(
            core.settings.SECRET_KEY_FALLBACKS,
            ["old-key", "older-key"],
        )

    def test_no_fallback_keys_by_default(self):
        self._reload_with({"DJANGO_DEBUG": "false", "DJANGO_SECRET_KEY": "k"})

        self.assertEqual(core.settings.SECRET_KEY_FALLBACKS, [])


class CacheSettingsEnvironmentTests(SimpleTestCase):
    def test_database_cache_when_cache_table_set(self):
        """DJANGO_CACHE_TABLE set → DatabaseCache with correct LOCATION."""
        cache_environment = {
            "DJANGO_CACHE_TABLE": "wf_cache",
        }
        had_caches = "CACHES" in core.settings.__dict__
        original_caches = core.settings.__dict__.get("CACHES")

        try:
            with mock.patch.dict("os.environ", cache_environment):
                importlib.reload(core.settings)
                cache = core.settings.CACHES["default"]

                self.assertEqual(
                    cache["BACKEND"],
                    "django.core.cache.backends.db.DatabaseCache",
                )
                self.assertEqual(
                    cache["LOCATION"],
                    "wf_cache",
                )
        finally:
            importlib.reload(core.settings)
            if had_caches:
                core.settings.CACHES = original_caches
            else:
                core.settings.__dict__.pop("CACHES", None)

    def test_default_cache_when_cache_table_unset(self):
        """DJANGO_CACHE_TABLE unset → Django's default LocMemCache applies."""
        had_caches = "CACHES" in core.settings.__dict__
        original_caches = core.settings.__dict__.get("CACHES")

        try:
            with (
                mock.patch("dotenv.load_dotenv"),
                # A cleared environment now means "production with no secret",
                # which settings refuses to start with, so supply the one
                # required variable. This test is about CACHES, not secrets.
                mock.patch.dict(
                    "os.environ",
                    {"DJANGO_SECRET_KEY": "test-key-for-settings-reload"},
                    clear=True,
                ),
            ):
                core.settings.__dict__.pop("CACHES", None)
                importlib.reload(core.settings)

                self.assertIsNone(core.settings.CACHE_TABLE)
                self.assertNotIn("CACHES", core.settings.__dict__)

                django_settings = Settings("core.settings")
                self.assertEqual(
                    django_settings.CACHES["default"]["BACKEND"],
                    "django.core.cache.backends.locmem.LocMemCache",
                )
        finally:
            importlib.reload(core.settings)
            if had_caches:
                core.settings.CACHES = original_caches
            else:
                core.settings.__dict__.pop("CACHES", None)


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

    def test_login_failure_shows_non_field_error(self) -> None:
        # WCAG 3.3.1 Error Identification: form-level errors must be rendered
        response = self.client.post(
            reverse("login"),
            {"username": "nobody@example.com", "password": "wrong"},
        )
        self.assertContains(response, 'role="alert"')
        self.assertContains(response, "Please enter a correct")

    def test_registration_field_errors_are_linked_to_inputs(self) -> None:
        response = self.client.post(
            reverse("django_registration_register"),
            {
                "email": "new@example.com",
                "first_name": "Test",
                "last_name": "User",
                "password1": "Mismatch-One-7731",
                "password2": "Mismatch-Two-8842",
            },
        )
        html = response.content.decode()
        # Django points aria-describedby at these ids; they must exist
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
