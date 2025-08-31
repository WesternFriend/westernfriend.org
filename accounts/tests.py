from unittest.mock import PropertyMock, patch
from django.conf import settings
from django.test import TestCase, RequestFactory
from django.urls import reverse, NoReverseMatch
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


class HoneypotTest(TestCase):
    def test_register_page_contains_honeypot_field(self):
        response = self.client.get(reverse("django_registration_register"))
        self.assertContains(
            response,
            settings.HONEYPOT_FIELD_NAME,
        )


class CustomLoginViewTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()

    def _call_get_success_url(self, next_value: str):
        request = self.factory.get("/accounts/login/", {"next": next_value})
        view = CustomLoginView()
        view.request = request
        return view.get_success_url()

    def test_fallback_when_reverse_missing_and_next_is_admin(self):
        # Patch accounts.views.reverse to raise NoReverseMatch to trigger fallback
        with patch("accounts.views.reverse", side_effect=NoReverseMatch()):
            url = self._call_get_success_url("/admin/")
        # Should fall back to LOGIN_REDIRECT_URL instead of admin
        self.assertEqual(url, settings.LOGIN_REDIRECT_URL)

    def test_redirect_allows_safe_non_admin_next_when_reverse_missing(self):
        with patch("accounts.views.reverse", side_effect=NoReverseMatch()):
            url = self._call_get_success_url("/some-safe-page/")
        self.assertEqual(url, "/some-safe-page/")
