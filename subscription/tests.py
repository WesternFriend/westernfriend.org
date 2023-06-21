import datetime
import braintree
from django.test import TestCase

from accounts.models import User
from subscription.models import Subscription
from .views import handle_subscription_webhook


class SubscriptionWebhookTestCase(TestCase):
    def setUp(self) -> None:
        braintree_configuration = braintree.Configuration(
            braintree.Environment.Sandbox,  # type: ignore
            merchant_id="123",
            public_key="123",
            private_key="123",
        )
        # create a mock BraintreeSubscription
        self.braintree_subscription_with_paid_through_date = braintree.Subscription(
            gateway=braintree.BraintreeGateway(braintree_configuration),
            attributes={
                "id": "test_subscription_id",
                "paid_through_date": "2022-07-01",
            },
        )

        self.braintree_subscription_without_paid_through_date = braintree.Subscription(
            gateway=braintree.BraintreeGateway(braintree_configuration),
            attributes={
                "id": "test_subscription_id",
            },
        )

        # Create a User and Subscription
        self.user = User.objects.create_user(  # type: ignore
            email="test@user.com",
            password="testpassword",
        )

        self.subscription = Subscription.objects.create(
            user=self.user,
            braintree_subscription_id="test_subscription_id",
            end_date=datetime.date(2021, 1, 1),
        )

    def test_handle_subscription_webhook_with_paid_through_date(self) -> None:
        handle_subscription_webhook(
            self.braintree_subscription_with_paid_through_date,
        )

        self.subscription.refresh_from_db()

        self.assertEqual(
            self.subscription.end_date,
            datetime.date(2022, 7, 6),
        )

    def test_handle_subscription_webhook_without_paid_through_date(self) -> None:
        handle_subscription_webhook(
            self.braintree_subscription_without_paid_through_date,
        )

        self.subscription.refresh_from_db()

        self.assertEqual(
            self.subscription.end_date,
            datetime.date(2022, 1, 6),
        )

    def tearDown(self) -> None:
        self.subscription.delete()
        self.user.delete()
        return super().tearDown()
