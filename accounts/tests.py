import importlib
import re
import sys
from unittest import mock
from unittest.mock import PropertyMock, patch
from urllib.parse import parse_qs, urlsplit

import yaml
from django.conf import Settings, settings
from django.contrib.messages import get_messages
from django.core import mail, signing
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import resolve_url
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import NoReverseMatch, reverse
from django_registration.backends.activation import REGISTRATION_SALT
from wagtail.models import Page, Site

import core.settings
from accounts.views import CHECK_EMAIL_MESSAGE, CustomLoginView
from home.models import HomePage
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

    def test_surrounding_whitespace_is_preserved(self):
        """A padded key keeps signing exactly as it always has.

        Django has always used the env value verbatim, so a deployment whose
        key carries surrounding whitespace has been signing with it all along.
        Normalising here would silently rotate their key and invalidate every
        live session and reset token — the invisible breakage this change
        exists to prevent. Whitespace is validated (see the tests above) but
        never altered.
        """
        self._reload_with(
            {"DJANGO_DEBUG": "false", "DJANGO_SECRET_KEY": "  a-real-secret\n"},
        )

        self.assertEqual(core.settings.SECRET_KEY, "  a-real-secret\n")

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

    def test_tailwind_build_runs_without_a_key(self):
        """The build compiles the CSS before collectstatic, also without a secret."""
        with mock.patch.object(sys, "argv", ["manage.py", "tailwind", "build"]):
            self._reload_with({"DJANGO_DEBUG": "false"})

        self.assertTrue(core.settings.SECRET_KEY)

    def test_tailwind_start_still_fails_without_a_key(self):
        """Only the one-off build is exempt, not the watcher or dev server."""
        with (
            mock.patch.object(sys, "argv", ["manage.py", "tailwind", "dev"]),
            self.assertRaises(ImproperlyConfigured),
        ):
            self._reload_with({"DJANGO_DEBUG": "false"})

    def test_other_commands_still_fail_without_a_key(self):
        """The collectstatic exemption must not leak to anything that serves."""
        with (
            mock.patch.object(sys, "argv", ["manage.py", "migrate"]),
            self.assertRaises(ImproperlyConfigured),
        ):
            self._reload_with({"DJANGO_DEBUG": "false"})

    def test_fallback_keys_are_parsed_for_rotation(self):
        """Old keys keep existing sessions valid while a new key rolls out."""
        self._reload_with(
            {
                "DJANGO_DEBUG": "false",
                "DJANGO_SECRET_KEY": "new-key",
                "DJANGO_SECRET_KEY_FALLBACKS": "old-key,older-key,",
            },
        )

        self.assertEqual(
            core.settings.SECRET_KEY_FALLBACKS,
            ["old-key", "older-key"],
        )

    def test_fallback_keys_are_kept_verbatim(self):
        """A fallback must equal the previous key byte for byte.

        If the key being rotated out carried whitespace, only a verbatim
        fallback can still match the signatures it minted — stripping here
        would make rotation silently fail for exactly the deployments the
        fallback mechanism exists to protect.
        """
        self._reload_with(
            {
                "DJANGO_DEBUG": "false",
                "DJANGO_SECRET_KEY": "new-key",
                "DJANGO_SECRET_KEY_FALLBACKS": "  padded-old-key\n",
            },
        )

        self.assertEqual(core.settings.SECRET_KEY_FALLBACKS, ["  padded-old-key\n"])

    def test_no_fallback_keys_by_default(self):
        self._reload_with({"DJANGO_DEBUG": "false", "DJANGO_SECRET_KEY": "k"})

        self.assertEqual(core.settings.SECRET_KEY_FALLBACKS, [])


class CacheSettingsEnvironmentTests(SimpleTestCase):
    def test_database_cache_when_enabled(self):
        """DJANGO_DATABASE_CACHE=True → DatabaseCache on the django_cache table."""
        had_caches = "CACHES" in core.settings.__dict__
        original_caches = core.settings.__dict__.get("CACHES")

        try:
            for value in ("True", "true", "1"):
                with (
                    self.subTest(value=value),
                    mock.patch.dict("os.environ", {"DJANGO_DATABASE_CACHE": value}),
                ):
                    importlib.reload(core.settings)
                    cache = core.settings.CACHES["default"]

                    self.assertEqual(
                        cache["BACKEND"],
                        "django.core.cache.backends.db.DatabaseCache",
                    )
                    self.assertEqual(cache["LOCATION"], "django_cache")
                    renditions = core.settings.CACHES["renditions"]
                    self.assertEqual(
                        renditions["BACKEND"],
                        "django.core.cache.backends.locmem.LocMemCache",
                    )
                    self.assertEqual(renditions["LOCATION"], "renditions")
                    self.assertEqual(
                        renditions["TIMEOUT"],
                        core.settings.RENDITION_CACHE_TIMEOUT,
                    )
        finally:
            importlib.reload(core.settings)
            if had_caches:
                core.settings.CACHES = original_caches
            else:
                core.settings.__dict__.pop("CACHES", None)

    def test_default_cache_when_database_cache_not_enabled(self):
        """DJANGO_DATABASE_CACHE unset or false → LocMemCache applies."""
        had_caches = "CACHES" in core.settings.__dict__
        original_caches = core.settings.__dict__.get("CACHES")

        try:
            for environment in ({}, {"DJANGO_DATABASE_CACHE": "False"}):
                with (
                    self.subTest(environment=environment),
                    mock.patch("dotenv.load_dotenv"),
                    # A cleared environment now means "production with no
                    # secret", which settings refuses to start with, so supply
                    # the one required variable alongside each subTest's own.
                    # This test is about CACHES, not secrets.
                    mock.patch.dict(
                        "os.environ",
                        {
                            **environment,
                            "DJANGO_SECRET_KEY": "test-key-for-settings-reload",
                        },
                        clear=True,
                    ),
                ):
                    core.settings.__dict__.pop("CACHES", None)
                    importlib.reload(core.settings)

                    self.assertFalse(core.settings.USE_DATABASE_CACHE)
                    self.assertNotIn("CACHES", core.settings.__dict__)

                    django_settings = Settings("core.settings")
                    self.assertEqual(
                        django_settings.CACHES["default"]["BACKEND"],
                        "django.core.cache.backends.locmem.LocMemCache",
                    )
                    self.assertNotIn("renditions", django_settings.CACHES)
        finally:
            importlib.reload(core.settings)
            if had_caches:
                core.settings.CACHES = original_caches
            else:
                core.settings.__dict__.pop("CACHES", None)

    def test_pre_deploy_job_creates_the_configured_cache_table(self):
        """The pre-deploy job names the table explicitly, so it is created
        even while the database cache is switched off."""
        app_spec = yaml.safe_load(
            (core.settings.BASE_DIR / ".do/deploy.template.yaml").read_text(),
        )
        pre_deploy_jobs = [
            job for job in app_spec["spec"]["jobs"] if job["kind"] == "PRE_DEPLOY"
        ]
        self.assertEqual(len(pre_deploy_jobs), 1)
        run_command = pre_deploy_jobs[0]["run_command"]
        self.assertIn("python manage.py migrate", run_command)
        self.assertIn(
            f"python manage.py createcachetable {core.settings.DATABASE_CACHE_TABLE}",
            run_command,
        )


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


class RegistrationConfirmationTest(TestCase):
    """After registering, people are told to check their email (#961)."""

    def _register(self, **kwargs):
        return self.client.post(
            reverse("django_registration_register"),
            {
                "email": "new@example.com",
                "first_name": "Test",
                "last_name": "User",
                "password1": "Correct-Horse-7731",
                "password2": "Correct-Horse-7731",
            },
            **kwargs,
        )

    def test_registering_queues_the_check_email_message(self) -> None:
        response = self._register()

        self.assertRedirects(response, "/", fetch_redirect_response=False)
        queued = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(queued, [CHECK_EMAIL_MESSAGE])

    def test_message_reads_as_one_sentence_block(self) -> None:
        # It is shown in a single alert, so no line breaks or source
        # indentation should end up inside it.
        self.assertNotIn("\n", CHECK_EMAIL_MESSAGE)
        self.assertNotIn("  ", CHECK_EMAIL_MESSAGE)
        self.assertIn("check your email for a message from us", CHECK_EMAIL_MESSAGE)

    def test_message_is_shown_on_the_page_they_land_on(self) -> None:
        Site.objects.all().delete()
        root = Page.objects.get(depth=1)
        home = root.add_child(
            instance=HomePage(title="Home", slug="registration-home"),
        )
        Site.objects.create(
            hostname="testserver",
            root_page=home,
            is_default_site=True,
        )
        Site.clear_site_root_paths_cache()
        self.addCleanup(Site.clear_site_root_paths_cache)

        response = self._register(follow=True)

        self.assertRedirects(response, "/")
        self.assertContains(response, "please check your email for a message")

    def test_activation_email_explains_how_to_finish(self) -> None:
        self._register()

        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        self.assertIn("To complete your registration, click on the link below.", body)
        self.assertIn("copy and paste it into your browser", body)

        # The link must carry a real key for this user, not just the
        # "activation_key=" prefix: an empty or garbled key would still pass a
        # substring check.
        links = re.findall(r"https?://\S+", body)
        self.assertEqual(len(links), 1, body)
        url = urlsplit(links[0])
        self.assertEqual(url.path, reverse("django_registration_activate"))
        keys = parse_qs(url.query).get("activation_key", [])
        self.assertEqual(len(keys), 1, links[0])
        user = User.objects.get(email="new@example.com")
        self.assertEqual(
            signing.loads(keys[0], salt=REGISTRATION_SALT),
            user.get_username(),
        )
