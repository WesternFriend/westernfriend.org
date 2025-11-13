from unittest.mock import PropertyMock, patch
from django.conf import settings
from django.test import TestCase, RequestFactory, override_settings
from django.shortcuts import resolve_url
from django.urls import reverse, NoReverseMatch
from django.core import mail
from .models import User
from subscription.models import Subscription
from accounts.views import CustomLoginView


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
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_sends_text_and_html(self):
        user = User.objects.create_user(email="pr@example.com", password="x")  # noqa: S106 (test-only)
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
        html_body, html_mime = msg.alternatives[0]
        self.assertTrue(str(html_body).strip())
