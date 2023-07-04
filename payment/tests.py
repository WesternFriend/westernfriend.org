from datetime import date
from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch
from braintree import ErrorResult, SuccessfulResult, Transaction
from braintree import Subscription as BraintreeSubscription
from django.http import HttpRequest, HttpResponse

from django.test import Client, RequestFactory
from django.urls import reverse

from donations.models import Donation
from orders.models import Order
from subscription.models import Subscription
from .views import (
    MAGAZINE_SUBSCRIPTION_PLAN_ID,
    RECURRING_DONATION_PLAN_IDS,
    render_payment_processing_page,
    process_braintree_subscription,
    process_braintree_transaction,
    process_braintree_recurring_donation,
    process_braintree_single_donation,
    process_donation_payment,
    process_bookstore_order_payment,
    process_subscription_payment,
)


class TestPaymentProcessingPage(TestCase):
    @patch("braintree.ClientToken.generate")
    def test_render_payment_processing_page(self, mock_generate: Mock) -> None:
        # Mock Braintree token generator to return a fake token
        mock_generate.return_value = "fake_token"

        # Create a GET request with RequestFactory
        factory = RequestFactory()
        mock_request = factory.get("/fake-url")

        # Execute function with mock request and arbitrary payment total
        response = render_payment_processing_page(mock_request, 100)

        # Test if the response is 200 OK.
        self.assertEqual(response.status_code, 200)

        # Test if the correct context is used in the rendered template
        # by checking if the context variables are present in the response content.
        self.assertIn(b"fake_token", response.content)
        self.assertIn(b"100", response.content)


class TestProcessBraintreeSubscription(TestCase):
    @patch("braintree.CustomerGateway.create")
    @patch("braintree.SubscriptionGateway.create")
    def test_process_braintree_subscription(
        self, mock_subscription_create: Mock, mock_customer_create: Mock
    ) -> None:
        # Mock Braintree subscription creation to return a fake subscription
        mock_subscription_create.return_value = SuccessfulResult(
            {
                "subscription": MagicMock(),  # this represents a Subscription object
            }
        )
        mock_subscription_create.return_value.subscription.id = "fake_subscription"  # type: ignore # noqa: E501

        # Mock Braintree customer creation to return a successful result with a mock customer  # noqa: E501
        mock_customer = MagicMock()
        mock_payment_method = MagicMock()
        mock_payment_method.token = "fake_token"
        mock_customer.payment_methods = [mock_payment_method]

        mock_customer_create.return_value = SuccessfulResult(
            {
                "customer": mock_customer,
            }
        )

        # Execute function with arbitrary subscription data
        subscription = process_braintree_subscription(
            first_name="John",
            last_name="Doe",
            plan_id="fake_plan_id",
            price=100,
            recurring=True,
            nonce="fake_nonce",
        )

        # Test if the subscription is created
        self.assertEqual(subscription.subscription.id, "fake_subscription")  # type: ignore  # noqa: E501

    @patch("payment.views.get_object_or_404")
    @patch("payment.views.process_braintree_subscription")
    @patch("payment.views.redirect")
    def test_process_braintree_subscription_non_recurring(
        self,
        mock_redirect: Mock,
        mock_process_subscription: Mock,
        mock_get_object_or_404: Mock,
    ) -> None:
        # Arrange
        mock_request = HttpRequest()
        mock_request.method = "POST"
        mock_request.POST["payment_method_nonce"] = "fake_nonce"

        mock_subscription = Mock(spec=Subscription)
        mock_subscription.subscriber_given_name = "Test"
        mock_subscription.subscriber_family_name = "User"
        mock_subscription.price = 10
        mock_subscription.recurring = False
        mock_get_object_or_404.return_value = mock_subscription

        mock_result = Mock()
        mock_result.is_success = True
        mock_result.transaction.id = "test_id"
        mock_result.subscription = Mock()
        mock_result.subscription.paid_through_date = date(2023, 12, 31)
        mock_process_subscription.return_value = mock_result

        # Act
        response = process_subscription_payment(mock_request, 1)

        # Assert
        mock_process_subscription.assert_called_once_with(
            first_name="Test",
            last_name="User",
            plan_id=MAGAZINE_SUBSCRIPTION_PLAN_ID,
            price=10,
            recurring=False,
            nonce="fake_nonce",
        )
        self.assertEqual(response, mock_redirect.return_value)


class TestProcessBraintreeTransaction(TestCase):
    @patch.object(Transaction, "sale")
    def test_process_braintree_transaction_success(self, mock_sale: Mock) -> None:
        # Mock the transaction sale to return a successful result with a mock transaction  # noqa: E501
        mock_sale.return_value = SuccessfulResult(
            {
                "transaction": MagicMock(),  # this represents a Transaction object
            }
        )
        mock_sale.return_value.transaction.id = "fake_transaction_id"  # type: ignore

        # Execute function with arbitrary transaction data
        result = process_braintree_transaction(
            amount=100,
            nonce="fake_nonce",
        )

        # Test if the transaction was successful
        self.assertTrue(result.is_success)
        self.assertEqual(result.transaction.id, "fake_transaction_id")  # type: ignore

    @patch.object(Transaction, "sale")
    def test_process_braintree_transaction_failure(self, mock_sale: Mock) -> None:
        # Mock the transaction sale to return an error result
        mock_gateway = MagicMock()  # Mock gateway object
        mock_sale.return_value = ErrorResult(
            mock_gateway,
            {
                "message": "Error message",
                "errors": {},  # Add this line
            },
        )

        # Execute function with arbitrary transaction data
        result = process_braintree_transaction(
            amount=100,
            nonce="fake_nonce",
        )

        # Test if the transaction failed
        self.assertFalse(result.is_success)
        self.assertEqual(result.message, "Error message")  # type: ignore


class TestProcessBraintreeRecurringDonation(TestCase):
    @patch("payment.views.process_braintree_subscription")
    @patch("payment.views.redirect")
    def test_process_braintree_recurring_donation_success(
        self,
        mock_redirect: Mock,
        mock_process_subscription: Mock,
    ) -> None:
        # Create a mock donation object
        mock_donation = MagicMock()
        mock_donation.get_total_cost.return_value = 100
        mock_donation.recurrence = "monthly"
        mock_donation.recurring = True
        mock_donation.paid = False
        mock_donation.donor_given_name = "John"
        mock_donation.donor_family_name = "Doe"

        # Mock SuccessfulResult from Braintree
        mock_result = SuccessfulResult({"subscription": MagicMock(id="test_id")})
        mock_process_subscription.return_value = mock_result

        # Mock redirect
        mock_redirect.return_value = HttpResponse()

        process_braintree_recurring_donation(mock_donation, "fake_nonce")

        # Assert donation has been paid and ID is set
        self.assertTrue(mock_donation.paid)
        self.assertEqual(mock_donation.braintree_subscription_id, "test_id")

        # Assert process_braintree_subscription has been called with correct parameters
        mock_process_subscription.assert_called_once_with(
            first_name=mock_donation.donor_given_name,
            last_name=mock_donation.donor_family_name,
            plan_id=RECURRING_DONATION_PLAN_IDS[mock_donation.recurrence],
            price=mock_donation.get_total_cost.return_value,
            recurring=mock_donation.recurring,
            nonce="fake_nonce",
        )

        # Assert redirect function was called with 'payment:done'
        mock_redirect.assert_called_once_with("payment:done")

    @patch("payment.views.process_braintree_subscription")
    @patch("payment.views.redirect")
    def test_process_braintree_recurring_donation_failure(
        self,
        mock_redirect: Mock,
        mock_process_subscription: Mock,
    ) -> None:
        # Create a mock donation object
        mock_donation = MagicMock(spec=Donation)
        mock_donation.get_total_cost.return_value = 100
        mock_donation.recurrence = "monthly"
        mock_donation.recurring = True
        mock_donation.paid = False
        mock_donation.donor_given_name = "John"
        mock_donation.donor_family_name = "Doe"
        mock_donation.braintree_subscription_id = None

        # Mock ValidationError from Braintree
        mock_result = ErrorResult(None, {"errors": {}, "message": "Error message"})
        mock_process_subscription.return_value = mock_result

        # Mock redirect
        mock_redirect.return_value = HttpResponse()

        process_braintree_recurring_donation(mock_donation, "fake_nonce")

        # Assert donation has not been paid
        self.assertFalse(mock_donation.paid)
        self.assertIsNone(mock_donation.braintree_subscription_id)

        # Assert process_braintree_subscription has been called with correct parameters
        mock_process_subscription.assert_called_once_with(
            first_name=mock_donation.donor_given_name,
            last_name=mock_donation.donor_family_name,
            plan_id=RECURRING_DONATION_PLAN_IDS[mock_donation.recurrence],
            price=mock_donation.get_total_cost.return_value,
            recurring=mock_donation.recurring,
            nonce="fake_nonce",
        )

        # Assert redirect function was called with 'payment:canceled'
        mock_redirect.assert_called_once_with("payment:canceled")


class TestProcessBraintreeSingleDonation(TestCase):
    @patch("payment.views.process_braintree_transaction")
    @patch("payment.views.redirect")
    def test_process_braintree_single_donation_success(
        self,
        mock_redirect: Mock,
        mock_process_transaction: Mock,
    ) -> None:
        # Create a mock donation object
        mock_donation = MagicMock()
        mock_donation.amount = 100
        mock_donation.paid = False

        # Mock SuccessfulResult from Braintree
        mock_result = SuccessfulResult({"transaction": MagicMock(id="test_id")})
        mock_process_transaction.return_value = mock_result

        response = process_braintree_single_donation(
            donation=mock_donation, nonce="fake_nonce"
        )

        self.assertTrue(mock_donation.paid)
        self.assertEqual(mock_donation.braintree_transaction_id, "test_id")
        mock_redirect.assert_called_once_with("payment:done")
        self.assertEqual(response, mock_redirect.return_value)

    @patch("payment.views.process_braintree_transaction")
    @patch("payment.views.redirect")
    def test_process_braintree_single_donation_failure(
        self,
        mock_redirect: Mock,
        mock_process_transaction: Mock,
    ) -> None:
        # Create a mock donation object
        mock_donation = MagicMock()
        mock_donation.amount = 100
        mock_donation.paid = False
        mock_donation.braintree_transaction_id = None

        # Mock ErrorResult from Braintree
        mock_result = ErrorResult(None, {"errors": {}, "message": "Error message"})
        mock_process_transaction.return_value = mock_result

        response = process_braintree_single_donation(
            donation=mock_donation,
            nonce="fake_nonce",
        )

        self.assertFalse(mock_donation.paid)
        self.assertIsNone(mock_donation.braintree_transaction_id)
        mock_redirect.assert_called_once_with("payment:canceled")
        self.assertEqual(response, mock_redirect.return_value)


class TestProcessDonationPayment(TestCase):
    @patch("payment.views.get_object_or_404")
    @patch("payment.views.render_payment_processing_page")
    def test_process_donation_payment_GET(
        self,
        mock_render_page: Mock,
        mock_get_donation: Mock,
    ) -> None:
        mock_request = MagicMock(spec=HttpRequest)
        mock_request.method = "GET"

        mock_donation = Mock(spec=Donation)
        mock_get_donation.return_value = mock_donation

        response = process_donation_payment(mock_request, 1)

        mock_render_page.assert_called_once_with(
            request=mock_request,
            payment_total=mock_donation.get_total_cost(),
        )
        self.assertEqual(response, mock_render_page.return_value)

    @patch("payment.views.logger")
    @patch("payment.views.get_object_or_404")
    @patch("payment.views.render_payment_processing_page")
    @patch("payment.views.process_braintree_transaction")
    def test_process_donation_payment_POST_no_nonce(
        self,
        mock_process_transaction: Mock,
        mock_render_payment_page: Mock,
        mock_get_donation: Mock,
        mock_logger: Mock,
    ) -> None:
        mock_request = MagicMock(spec=HttpRequest)
        mock_request.method = "POST"
        mock_request.POST = {}

        mock_donation = Mock(spec=Donation)
        mock_get_donation.return_value = mock_donation

        mock_response = Mock(spec=HttpResponse)
        mock_render_payment_page.return_value = mock_response

        response = process_donation_payment(mock_request, 1)

        mock_render_payment_page.assert_called_once_with(
            request=mock_request,
            payment_total=mock_donation.get_total_cost.return_value,
        )
        # Assert logger.warning was called
        mock_logger.warning.assert_called_once_with(
            msg="Braintree donation payment failed: nonce is None"
        )
        self.assertEqual(response, mock_render_payment_page.return_value)

    @patch("payment.views.get_object_or_404")
    @patch("payment.views.process_braintree_recurring_donation")
    def test_process_donation_payment_POST_recurring(
        self,
        mock_process_recurring: Mock,
        mock_get_donation: Mock,
    ) -> None:
        mock_request = MagicMock(spec=HttpRequest)
        mock_request.method = "POST"
        mock_request.POST = {"payment_method_nonce": "nonce"}

        mock_donation = Mock(spec=Donation)
        mock_donation.recurring = True
        mock_get_donation.return_value = mock_donation

        response = process_donation_payment(mock_request, 1)

        mock_process_recurring.assert_called_once_with(mock_donation, "nonce")
        self.assertEqual(response, mock_process_recurring.return_value)

    @patch("payment.views.get_object_or_404")
    @patch("payment.views.process_braintree_single_donation")
    def test_process_donation_payment_POST_single(
        self,
        mock_process_single: Mock,
        mock_get_donation: Mock,
    ) -> None:
        mock_request = MagicMock(spec=HttpRequest)
        mock_request.method = "POST"
        mock_request.POST = {"payment_method_nonce": "nonce"}

        mock_donation = Mock(spec=Donation)
        mock_donation.recurring = False
        mock_get_donation.return_value = mock_donation

        response = process_donation_payment(mock_request, 1)

        mock_process_single.assert_called_once_with(mock_donation, "nonce")
        self.assertEqual(response, mock_process_single.return_value)


class TestProcessBookstoreOrderPayment(TestCase):
    @patch("payment.views.get_object_or_404")
    @patch("payment.views.render_payment_processing_page")
    def test_process_bookstore_order_payment_GET(
        self,
        mock_render_page: Mock,
        mock_get_order: Mock,
    ) -> None:
        mock_request = MagicMock(spec=HttpRequest)
        mock_request.method = "GET"

        mock_order = Mock(spec=Order)
        mock_get_order.return_value = mock_order

        response = process_bookstore_order_payment(mock_request, 1)

        mock_render_page.assert_called_once_with(
            request=mock_request,
            payment_total=mock_order.get_total_cost(),
        )
        self.assertEqual(response, mock_render_page.return_value)

    @patch("payment.views.logger")
    @patch("payment.views.get_object_or_404")
    @patch("payment.views.render_payment_processing_page")
    @patch("payment.views.process_braintree_transaction")
    def test_process_bookstore_order_payment_POST_no_nonce(
        self,
        mock_process_transaction: Mock,
        mock_render_payment_page: Mock,
        mock_get_order: Mock,
        mock_logger: Mock,
    ) -> None:
        mock_request = MagicMock(spec=HttpRequest)
        mock_request.method = "POST"
        mock_request.POST = {}

        mock_order = Mock(spec=Order)
        mock_order.get_total_cost.return_value = 123
        mock_get_order.return_value = mock_order

        mock_response = Mock(spec=HttpResponse)
        mock_render_payment_page.return_value = mock_response

        response = process_bookstore_order_payment(mock_request, 1)

        mock_render_payment_page.assert_called_once_with(
            request=mock_request,
            payment_total=mock_order.get_total_cost.return_value,
        )
        # Assert logger.warning was called
        mock_logger.warning.assert_called_once_with(
            msg="Braintree order payment failed: nonce is None"
        )
        self.assertEqual(response, mock_render_payment_page.return_value)

    @patch("payment.views.get_object_or_404")
    @patch("payment.views.redirect")
    @patch("payment.views.process_braintree_transaction")
    def test_process_bookstore_order_payment_POST_success(
        self, mock_process_transaction: Mock, mock_redirect: Mock, mock_get_order: Mock
    ) -> None:
        mock_request = MagicMock(spec=HttpRequest)
        mock_request.method = "POST"
        mock_request.POST = {"payment_method_nonce": "nonce"}

        mock_order = Mock(spec=Order)
        mock_get_order.return_value = mock_order

        mock_result = Mock()
        mock_result.is_success = True
        mock_result.transaction.id = "transaction_id"
        mock_process_transaction.return_value = mock_result

        response = process_bookstore_order_payment(mock_request, 1)

        self.assertTrue(mock_order.paid)
        self.assertEqual(mock_order.braintree_transaction_id, "transaction_id")
        mock_redirect.assert_called_once_with("payment:done")
        self.assertEqual(response, mock_redirect.return_value)

    @patch("payment.views.get_object_or_404")
    @patch("payment.views.process_braintree_transaction")
    @patch("payment.views.redirect")
    def test_process_bookstore_order_payment_POST_failure(
        self,
        mock_redirect: MagicMock,
        mock_process_transaction: MagicMock,
        mock_get_object_or_404: MagicMock,
    ) -> None:
        # Mock order
        mock_order = MagicMock()
        mock_order.get_total_cost.return_value = 100
        mock_order.paid = False
        mock_order.braintree_transaction_id = None
        mock_order.id = 1

        # Make get_object_or_404 return the mock_order when called.
        mock_get_object_or_404.return_value = mock_order

        # Mock request
        mock_request = MagicMock(spec=HttpRequest)
        mock_request.method = "POST"
        mock_request.POST = {"payment_method_nonce": "fake_nonce"}

        # Mock unsuccessful Braintree transaction
        mock_result = ErrorResult(None, {"message": "Error message", "errors": {}})
        mock_process_transaction.return_value = mock_result

        # Mock redirect
        mock_redirect.return_value = HttpResponse()

        process_bookstore_order_payment(mock_request, mock_order.id)

        # Assert order has not been paid
        self.assertFalse(mock_order.paid)
        self.assertIsNone(mock_order.braintree_transaction_id)

        # Assert process_braintree_transaction has been called with correct parameters
        mock_process_transaction.assert_called_once_with(
            amount=mock_order.get_total_cost.return_value,
            nonce=mock_request.POST.get("payment_method_nonce"),
        )

        # Assert redirect function was called with 'payment:canceled'
        mock_redirect.assert_called_once_with("payment:canceled")


class TestProcessSubscriptionPayment(TestCase):
    @patch("payment.views.braintree_gateway.customer.create")
    def test_process_braintree_subscription_customer_error(self, mock_create_customer):
        # Arrange
        first_name = "Test"
        last_name = "User"
        plan_id = "test_plan_id"
        price = 10
        recurring = False
        nonce = "fake_nonce"

        customer_error_result = ErrorResult(
            None,
            {"message": "Error message", "errors": {}},
        )

        # Mock the create function to return an error
        mock_create_customer.return_value = customer_error_result

        # Act
        result = process_braintree_subscription(
            first_name=first_name,
            last_name=last_name,
            plan_id=plan_id,
            price=price,
            recurring=recurring,
            nonce=nonce,
        )

        # Assert
        mock_create_customer.assert_called_once_with(
            {
                "first_name": first_name,
                "last_name": last_name,
                "payment_method_nonce": nonce,
            }
        )
        self.assertIsInstance(result, ErrorResult)
        self.assertEqual(result.message, "Error message")

    @patch("payment.views.get_object_or_404")
    @patch("payment.views.process_braintree_subscription")
    @patch("payment.views.redirect")
    def test_process_subscription_payment_POST_success(
        self,
        mock_redirect: Mock,
        mock_process_subscription: Mock,
        mock_get_object_or_404: Mock,
    ) -> None:
        # Arrange
        mock_request = HttpRequest()
        mock_request.method = "POST"
        mock_request.POST["payment_method_nonce"] = "fake_nonce"
        mock_subscription = MagicMock(spec=Subscription)
        mock_subscription.subscriber_given_name = "Test"
        mock_subscription.subscriber_family_name = "User"
        mock_subscription.price = 10
        mock_subscription.recurring = False
        mock_subscription.get_total_cost.return_value = 10
        mock_get_object_or_404.return_value = mock_subscription

        # Create a mock BraintreeSubscription object
        mock_braintree_subscription = MagicMock(spec=BraintreeSubscription)
        mock_braintree_subscription.id = "test_id"

        # Mock SuccessfulResult from Braintree
        mock_result = SuccessfulResult(
            {
                "transaction": {"id": "test_id"},
                "subscription": mock_braintree_subscription,
            }
        )
        mock_process_subscription.return_value = mock_result

        # Act
        response = process_subscription_payment(mock_request, subscription_id=1)

        # Assert
        mock_process_subscription.assert_called_once_with(
            first_name="Test",
            last_name="User",
            plan_id=MAGAZINE_SUBSCRIPTION_PLAN_ID,
            price=10,
            recurring=False,
            nonce="fake_nonce",
        )
        self.assertTrue(mock_subscription.paid)
        self.assertEqual(mock_subscription.braintree_subscription_id, "test_id")
        mock_redirect.assert_called_once_with("payment:done")
        self.assertEqual(response, mock_redirect.return_value)

    @patch("payment.views.get_object_or_404")
    @patch("payment.views.process_braintree_subscription")
    @patch("payment.views.redirect")
    def test_process_subscription_payment_POST_failure(
        self,
        mock_redirect: Mock,
        mock_process_subscription: Mock,
        mock_get_object_or_404: Mock,
    ) -> None:
        # Arrange
        mock_request = HttpRequest()
        mock_request.method = "POST"
        mock_request.POST["payment_method_nonce"] = "fake_nonce"
        mock_subscription = MagicMock(spec=Subscription)
        mock_subscription.paid = False  # <--- set paid attribute to False
        mock_subscription.subscriber_given_name = "Test"
        mock_subscription.subscriber_family_name = "User"
        mock_subscription.price = 10
        mock_subscription.recurring = False
        mock_subscription.get_total_cost.return_value = 10
        mock_get_object_or_404.return_value = mock_subscription

        # Mock ErrorResult from Braintree
        mock_result = ErrorResult(None, {"message": "Error message", "errors": {}})
        mock_process_subscription.return_value = mock_result

        # Act
        response = process_subscription_payment(mock_request, subscription_id=1)

        # Assert
        self.assertFalse(mock_subscription.paid)  # Now, this assertion should pass.
        mock_redirect.assert_called_once_with("payment:canceled")
        self.assertEqual(response, mock_redirect.return_value)

    @patch("subscription.views.calculate_end_date_from_braintree_subscription")
    @patch("payment.views.get_object_or_404")
    @patch("payment.views.render_payment_processing_page")
    @patch("payment.views.logger")
    def test_process_subscription_payment_POST_no_nonce(
        self,
        mock_logger: MagicMock,
        mock_render: MagicMock,
        mock_get_object_or_404: MagicMock,
        mock_calculate_end_date: MagicMock,
    ) -> None:
        # Mock subscription
        mock_subscription = MagicMock()
        mock_subscription.get_total_cost.return_value = 100
        mock_subscription.paid = False
        mock_subscription.braintree_subscription_id = None
        mock_subscription.id = 1  # Set the return value for mock_subscription.id

        # Make get_object_or_404 return the mock_subscription when called.
        mock_get_object_or_404.return_value = mock_subscription

        # Mock request
        mock_request = MagicMock(spec=HttpRequest)
        mock_request.method = "POST"
        mock_request.POST = {}  # No "payment_method_nonce" in POST data

        # Mock render
        mock_render.return_value = HttpResponse()

        response = process_subscription_payment(mock_request, mock_subscription.id)

        # Assert subscription has not been paid
        self.assertFalse(mock_subscription.paid)
        self.assertIsNone(mock_subscription.braintree_subscription_id)

        # Assert logger.warning was called
        mock_logger.warning.assert_called_once_with(
            msg="Braintree subscription payment failed: nonce is None"
        )

        # Assert render_payment_processing_page was called
        mock_render.assert_called_once_with(
            request=mock_request, payment_total=mock_subscription.get_total_cost()
        )

        # Assert response is instance of HttpResponse
        self.assertIsInstance(response, HttpResponse)

    @patch("payment.views.get_object_or_404")
    @patch("payment.views.render_payment_processing_page")
    def test_process_subscription_payment_GET(
        self,
        mock_render_payment_processing_page: Mock,
        mock_get_object_or_404: Mock,
    ) -> None:
        # Arrange
        mock_request = HttpRequest()
        mock_request.method = "GET"
        mock_subscription = MagicMock(spec=Subscription)
        mock_subscription.subscriber_given_name = "Test"
        mock_subscription.subscriber_family_name = "User"
        mock_subscription.price = 10
        mock_subscription.recurring = False
        mock_subscription.get_total_cost.return_value = 10
        mock_get_object_or_404.return_value = mock_subscription

        # Act
        response = process_subscription_payment(mock_request, subscription_id=1)

        # Assert
        mock_render_payment_processing_page.assert_called_once_with(
            request=mock_request, payment_total=mock_subscription.get_total_cost()
        )
        self.assertEqual(response, mock_render_payment_processing_page.return_value)


class TestPaymentViews(TestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_payment_done_view(self) -> None:
        response = self.client.get(reverse("payment:done"))
        self.assertEqual(response.status_code, 200)

    def test_payment_canceled_view(self) -> None:
        response = self.client.get(reverse("payment:canceled"))
        self.assertEqual(response.status_code, 200)
