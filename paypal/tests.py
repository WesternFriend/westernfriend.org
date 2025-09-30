from http import HTTPStatus
import json
from unittest import mock
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from requests.exceptions import HTTPError
from accounts.models import User

from orders.factories import OrderFactory
from orders.models import Order
from subscription.models import Subscription

from .auth import (
    get_auth_token,
    construct_paypal_auth_headers,
)
from .orders import (
    create_order,
    capture_order,
)
from .subscriptions import (
    get_subscription,
    subscription_is_active,
)
from .models import (
    PayPalError,
)


class GetAuthTokenTest(TestCase):
    @mock.patch("paypal.auth.requests.post")
    def test_get_auth_token_success(self, mock_post):
        # Mock successful API response
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "some_token"}
        mock_post.return_value = mock_response

        # Test function
        result = get_auth_token()
        self.assertEqual(result, "some_token")

    @mock.patch("paypal.auth.requests.post")
    def test_get_auth_token_failure(self, mock_post):
        # Mock failed API response
        mock_response = mock.Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = HTTPError()
        mock_post.return_value = mock_response

        # Test function should raise an error
        with self.assertRaises(PayPalError):
            get_auth_token()


class ConstructPayPalAuthHeadersTest(TestCase):
    @mock.patch("paypal.auth.get_auth_token")
    def test_construct_paypal_auth_headers(self, mock_get_auth_token):
        # Mock get_auth_token to return a sample token
        mock_get_auth_token.return_value = "sample_token"

        # Call the function and get the result
        result = construct_paypal_auth_headers()

        # Validate the result
        expected_result = {
            "Authorization": "Bearer sample_token",
            "Content-Type": "application/json",
        }
        self.assertEqual(result, expected_result)


class CreateOrderTest(TestCase):
    @mock.patch("paypal.orders.requests.post")
    @mock.patch("paypal.orders.construct_paypal_auth_headers")
    def test_create_order_success(self, mock_construct_headers, mock_post):
        # Mock the construct_paypal_auth_headers function
        mock_construct_headers.return_value = {
            "Authorization": "Bearer sample_token",
            "Content-Type": "application/json",
        }

        # Mock the API response
        mock_response = mock.Mock()
        mock_response.json.return_value = {"order_id": "12345"}
        mock_post.return_value = mock_response

        # Call the function
        result = create_order(value_usd="100.00")

        # Validate the result
        self.assertEqual(result, {"order_id": "12345"})

    @mock.patch("paypal.orders.requests.post")
    @mock.patch("paypal.orders.construct_paypal_auth_headers")
    def test_create_order_failure(self, mock_construct_headers, mock_post):
        # Mock the construct_paypal_auth_headers function
        mock_construct_headers.return_value = {
            "Authorization": "Bearer sample_token",
            "Content-Type": "application/json",
        }

        # Mock the API response
        mock_response = mock.Mock()
        mock_response.raise_for_status.side_effect = HTTPError()
        mock_post.return_value = mock_response

        # Call the function - should raise an error
        with self.assertRaises(PayPalError):
            create_order(value_usd="100.00")


class CaptureOrderTest(TestCase):
    @mock.patch("paypal.orders.requests.post")
    @mock.patch("paypal.orders.construct_paypal_auth_headers")
    def test_capture_order_success(self, mock_construct_headers, mock_post):
        # Mock construct_paypal_auth_headers
        mock_construct_headers.return_value = {
            "Authorization": "Bearer sample_token",
            "Content-Type": "application/json",
        }

        # Mock successful API response
        mock_response = mock.Mock()
        mock_response.json.return_value = {"status": "COMPLETED"}
        mock_post.return_value = mock_response

        # Call function
        result = capture_order(paypal_order_id="12345")

        # Validate result
        self.assertEqual(result, {"status": "COMPLETED"})

    @mock.patch("paypal.orders.logger")
    @mock.patch("paypal.orders.requests.post")
    @mock.patch("paypal.orders.construct_paypal_auth_headers")
    def test_capture_order_failure(
        self,
        mock_construct_headers,
        mock_post,
        mock_logger,
    ):
        # Mock construct_paypal_auth_headers
        mock_construct_headers.return_value = {
            "Authorization": "Bearer sample_token",
            "Content-Type": "application/json",
        }

        # Mock API failure
        mock_response = mock.Mock()
        mock_response.raise_for_status.side_effect = HTTPError()
        mock_post.return_value = mock_response

        # Call function and expect a PayPalError
        with self.assertRaises(PayPalError):  # Replace with your actual exception class
            capture_order(paypal_order_id="12345")

        # Check if logger.exception has been called
        mock_logger.exception.assert_called()


class GetSubscriptionTest(TestCase):
    @mock.patch("paypal.subscriptions.logger")
    @mock.patch("paypal.subscriptions.requests.get")
    @mock.patch("paypal.subscriptions.construct_paypal_auth_headers")
    def test_get_subscription_success(
        self,
        mock_construct_headers,
        mock_get,
        mock_logger,
    ):
        # Mock construct_paypal_auth_headers
        mock_construct_headers.return_value = {
            "Authorization": "Bearer sample_token",
            "Content-Type": "application/json",
        }

        # Mock successful API response
        mock_response = mock.Mock()
        mock_response.json.return_value = {"status": "ACTIVE"}
        mock_get.return_value = mock_response

        # Call function
        result = get_subscription(paypal_subscription_id="sub12345")

        # Validate result
        self.assertEqual(result, {"status": "ACTIVE"})

    @mock.patch("paypal.subscriptions.logger")
    @mock.patch("paypal.subscriptions.requests.get")
    @mock.patch("paypal.subscriptions.construct_paypal_auth_headers")
    def test_get_subscription_failure(
        self,
        mock_construct_headers,
        mock_get,
        mock_logger,
    ):
        # Mock construct_paypal_auth_headers
        mock_construct_headers.return_value = {
            "Authorization": "Bearer sample_token",
            "Content-Type": "application/json",
        }

        # Mock API failure
        mock_response = mock.Mock()
        mock_response.raise_for_status.side_effect = HTTPError()
        mock_get.return_value = mock_response

        # Call function and expect a PayPalError
        with self.assertRaises(PayPalError):  # Replace with your actual exception class
            get_subscription(paypal_subscription_id="sub12345")

        # Check if logger.exception has been called
        mock_logger.exception.assert_called()


class SubscriptionIsActiveTest(TestCase):
    @mock.patch("paypal.subscriptions.get_subscription")
    def test_subscription_is_active_cache_miss(self, mock_get_subscription):
        # Mock get_subscription for cache miss scenario
        mock_get_subscription.return_value = {"status": "ACTIVE"}

        # Ensure the cache is empty
        cache.clear()

        # Call function
        result = subscription_is_active(paypal_subscription_id="sub12345")

        # Validate result
        self.assertTrue(result)

    @mock.patch("paypal.subscriptions.get_subscription")
    def test_subscription_is_active_cache_hit(self, mock_get_subscription):
        # Populate the cache
        cache.set("paypal_subscription_sub12345", "ACTIVE", None)

        # Call function
        result = subscription_is_active(paypal_subscription_id="sub12345")

        # Validate result
        self.assertTrue(result)

        # Make sure get_subscription was not called
        mock_get_subscription.assert_not_called()

    @mock.patch("paypal.subscriptions.get_subscription")
    def test_subscription_is_not_active(self, mock_get_subscription):
        # Mock get_subscription for an inactive subscription
        mock_get_subscription.return_value = {"status": "INACTIVE"}

        # Ensure the cache is empty
        cache.clear()

        # Call function
        result = subscription_is_active(paypal_subscription_id="sub12345")

        # Validate result
        self.assertFalse(result)

    @mock.patch("paypal.subscriptions.get_subscription")
    def test_subscription_is_active_error(self, mock_get_subscription):
        # Mock get_subscription to raise a PayPalError
        mock_get_subscription.side_effect = PayPalError("Error message")

        # Ensure the cache is empty
        cache.clear()

        # Call function
        result = subscription_is_active(paypal_subscription_id="sub12345")

        # Validate result
        self.assertFalse(result)


class CreatePayPalOrderTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.order = OrderFactory()
        self.order.save()
        self.url = reverse("paypal:create_paypal_order")

    @mock.patch("paypal.views.create_order")
    def test_successful_paypal_order(self, mock_create_order):
        mock_create_order.return_value = {
            "id": "some_order_id",
        }
        payload = json.dumps(
            {
                "wf_order_id": self.order.id,
            },
        )
        response = self.client.post(
            self.url,
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            HTTPStatus.CREATED,
        )
        self.assertEqual(
            response.json(),
            {
                "paypal_order_id": "some_order_id",
            },
        )

    @mock.patch("paypal.views.create_order")
    def test_failed_paypal_order(self, mock_create_order):
        mock_create_order.side_effect = Exception("Some error")
        payload = json.dumps(
            {
                "wf_order_id": self.order.id,
            },
        )
        response = self.client.post(
            self.url,
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(
            response.status_code,
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )
        self.assertEqual(
            response.json(),
            {
                "error": "Error creating PayPal order.",
            },
        )

    def test_order_not_found(self):
        payload = json.dumps(
            {
                "wf_order_id": 9999,
            },
        )  # Non-existent Order ID
        response = self.client.post(
            self.url,
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            HTTPStatus.NOT_FOUND,
        )


class CapturePayPalOrderTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("paypal:capture_paypal_order")
        self.paypal_order_id = "sample_order_id"
        self.paypal_payment_id = "sample_payment_id"
        self.order = OrderFactory(
            paypal_order_id=self.paypal_order_id,
        )
        self.order.save()

    @mock.patch("paypal.views.capture_order")
    def test_successful_order_capture(self, mock_capture_order):
        assert Order.objects.filter(paypal_order_id=self.paypal_order_id).exists()
        mock_capture_order.return_value = {
            "status": "success",
            "id": self.paypal_payment_id,
        }
        payload = json.dumps(
            {
                "paypal_order_id": self.paypal_order_id,
                "paypal_payment_id": self.paypal_payment_id,
            },
        )
        response = self.client.post(
            self.url,
            data=payload,
            content_type="application/json",
        )
        mock_capture_order.assert_called()

        self.assertEqual(
            response.status_code,
            HTTPStatus.CREATED,
        )
        self.assertEqual(
            response.json(),
            {
                "id": self.paypal_payment_id,
                "status": "success",
            },
        )

    @mock.patch("paypal.views.capture_order")
    def test_failed_order_capture(self, mock_capture_order):
        mock_capture_order.side_effect = Exception("Some error")
        payload = json.dumps(
            {
                "paypal_order_id": self.paypal_order_id,
                "paypal_payment_id": self.paypal_payment_id,
            },
        )
        response = self.client.post(
            self.url,
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {
                "error": "Error capturing PayPal order.",
            },
        )


class LinkPayPalSubscriptionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("paypal:link_paypal_subscription")
        self.user = User.objects.create_user(
            email="testuser@email.com",
            password="testpass",
        )
        self.subscription_id = "sample_subscription_id"

    def test_successful_link(self):
        self.client.login(
            email="testuser@email.com",
            password="testpass",
        )
        payload = json.dumps(
            {
                "subscription_id": self.subscription_id,
            },
        )
        response = self.client.post(
            self.url,
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
        )
        self.assertEqual(
            response.json(),
            {
                "success": True,
            },
        )

        subscription = Subscription.objects.get(
            user=self.user,
        )
        self.assertEqual(
            subscription.paypal_subscription_id,
            self.subscription_id,
        )

    def test_unauthenticated_user(self):
        payload = json.dumps(
            {
                "subscriptionID": self.subscription_id,
            },
        )
        response = self.client.post(
            self.url,
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            HTTPStatus.FOUND,
        )  # Should redirect to login page

    def test_non_post_request(self):
        logged_in = self.client.login(
            email="testuser@email.com",
            password="testpass",
        )
        self.assertTrue(
            logged_in,
            "Client login failed",
        )  # Make sure the client is logged in

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            HTTPStatus.METHOD_NOT_ALLOWED,
        )
