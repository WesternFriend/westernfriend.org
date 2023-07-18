import datetime
from django.test import TestCase
from .models import User
from subscription.models import Subscription


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
        today = datetime.date.today()
        # Creating active subscription
        self.active_subscription = Subscription.objects.create(
            user=self.user,
            end_date=today + datetime.timedelta(days=7),
            paid=True,
        )
        # Creating expired subscription
        self.expired_subscription = Subscription.objects.create(
            user=self.user,
            end_date=today - datetime.timedelta(days=7),
        )

    def test_user_str_representation(self) -> None:
        # Test str representation returns email
        expected_str = "test@test.com"
        self.assertEqual(str(self.user), expected_str)

    def test_get_active_subscription(self) -> None:
        # Test if the active subscription is returned correctly
        active_subscription = self.user.get_active_subscription()
        self.assertIsNotNone(active_subscription)
        self.assertEqual(
            active_subscription,
            self.active_subscription,
        )
        self.assertGreaterEqual(
            active_subscription.end_date,  # type: ignore
            datetime.date.today(),
        )

    def test_get_active_subscription_with_no_subscription(self) -> None:
        # Test if None is returned when there is no active subscription
        self.user.subscriptions.all().delete()
        self.assertIsNone(self.user.get_active_subscription())

    def test_is_subscriber(self) -> None:
        # Test if is_subscriber returns true if user has subscription
        self.assertEqual(
            self.user.is_subscriber,
            True,
        )

    def test_is_not_subscriber(self) -> None:
        # Test if is_subscriber returns False if user has no subscription
        self.user.subscriptions.all().delete()
        self.assertEqual(
            self.user.is_subscriber,
            False,
        )
