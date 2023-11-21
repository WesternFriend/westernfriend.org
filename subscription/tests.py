from datetime import timedelta
from django.utils import timezone
from django.http import HttpRequest
from django.test import RequestFactory, TestCase

from unittest.mock import Mock, patch
from wagtail.models import Site

from accounts.factories import UserFactory
from accounts.models import User
from subscription.factories import SubscriptionFactory
from subscription.models import (
    ManageSubscriptionPage,
    Subscription,
    SubscriptionIndexPage,
)
from home.models import HomePage


class SubscriptionTestCase(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(  # type: ignore
            email="test@user.com",
            password="testpassword",  # pragma: no cover
        )

    def test_subscription_str(self) -> None:
        subscription = Subscription.objects.create(
            id=123,
            user=self.user,
            paypal_subscription_id="test_subscription_id",
        )

        expected_subscription_str = "Subscription 123"

        self.assertEqual(
            str(subscription),
            expected_subscription_str,
        )

        subscription.delete()

    def tearDown(self) -> None:
        self.user.delete()
        return super().tearDown()


class SubscriptionIndexPageTestCase(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()

        # Create a SubscriptionIndexPage instance and add it to the site tree
        self.site = Site.objects.get(is_default_site=True)

        self.home_page = HomePage(
            title="Home",
        )

        self.site.root_page.add_child(instance=self.home_page)
        self.subscription_index_page = SubscriptionIndexPage(
            title="Subscription",
        )
        self.home_page.add_child(instance=self.subscription_index_page)
        self.manage_subscription_page = ManageSubscriptionPage(
            title="Manage Subscription",
        )
        self.home_page.add_child(instance=self.manage_subscription_page)
        self.factory = RequestFactory()

    def test_subscription_index_page_str(self) -> None:
        subscription_index_page = SubscriptionIndexPage(title="Test Title")
        self.assertEqual(str(subscription_index_page), "Test Title")

    def test_get_request_serve_index_template(self) -> None:
        mock_request = self.factory.get("/")
        response = self.subscription_index_page.serve(mock_request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.template_name,  # type: ignore
            "subscription/index.html",
        )

    def test_redirect_subscriber_to_manage_subscription_page(self) -> None:
        subscription = SubscriptionFactory(
            user=self.user,
            paypal_subscription_id="",
            expiration_date=timezone.now().date() + timedelta(days=10),
        )
        subscription.save()
        # create mock HttpRequest
        mock_http_request = Mock(
            spec=HttpRequest,
            user=self.user,
        )

        response = self.subscription_index_page.serve(mock_http_request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            self.manage_subscription_page.url,
        )

    def tearDown(self) -> None:
        Subscription.objects.all().delete()
        self.subscription_index_page.delete()
        self.home_page.delete()
        self.site.delete()
        self.user.delete()  # type: ignore
        return super().tearDown()


class ManageSubscriptionPageTestCase(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()

        self.subscription = SubscriptionFactory(
            user=self.user,
            paypal_subscription_id="test_subscription_id",
        )

        # Create a SubscriptionIndexPage instance and add it to the site tree
        self.site = Site.objects.get(is_default_site=True)

        self.home_page = HomePage(
            title="Home",
        )

        self.site.root_page.add_child(instance=self.home_page)
        self.manage_subscription_page = ManageSubscriptionPage(
            title="Manage Subscription",
        )
        self.home_page.add_child(instance=self.manage_subscription_page)

        self.factory = RequestFactory()

    def tearDown(self) -> None:
        Subscription.objects.all().delete()
        self.manage_subscription_page.delete()
        self.home_page.delete()
        self.site.delete()
        self.user.delete()  # type: ignore
        return super().tearDown()

    def test_manage_subscription_with_user_subscriptions(self) -> None:
        # create mock HttpRequest
        mock_http_request = Mock(
            spec=HttpRequest,
            user=self.user,
        )

        context = self.manage_subscription_page.get_context(
            request=mock_http_request,
        )

        self.assertIsInstance(context["subscription"], Subscription)
        # assert that self.subscription is in the subscriptions queryset
        self.assertEqual(
            context["subscription"],
            self.subscription,
        )

    def test_manage_subscription_without_user_subscriptions(self) -> None:
        # create mock HttpRequest
        mock_http_request = Mock(
            spec=HttpRequest,
            user=UserFactory(),
        )

        context = self.manage_subscription_page.get_context(
            request=mock_http_request,
        )

        # assert that the context["subscription"] does not exist
        self.assertNotIn("subscription", context)


class TestSubscriptionModel(TestCase):
    @patch("subscription.models.paypal_subscriptions.subscription_is_active")
    def test_is_active_with_paypal_active(self, mock_is_active):
        mock_is_active.return_value = True
        subscription = Subscription(paypal_subscription_id="some_id")
        self.assertTrue(subscription.is_active)

    @patch("subscription.models.paypal_subscriptions.subscription_is_active")
    def test_is_active_with_paypal_inactive(self, mock_is_active):
        mock_is_active.return_value = False
        subscription = Subscription(paypal_subscription_id="some_id")
        self.assertFalse(subscription.is_active)

    def test_is_active_with_future_expiration(self):
        future_date = timezone.now().date() + timedelta(days=10)
        subscription = Subscription(expiration_date=future_date)
        self.assertTrue(subscription.is_active)

    def test_is_active_with_past_expiration(self):
        past_date = timezone.now().date() - timedelta(days=10)
        subscription = Subscription(expiration_date=past_date)
        self.assertFalse(subscription.is_active)

    def test_is_active_with_no_data(self):
        subscription = Subscription()
        self.assertFalse(subscription.is_active)
