from unittest import mock
from django.test import TestCase
from requests.exceptions import HTTPError

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
    def test_capture_order_failure(self, mock_construct_headers, mock_post, mock_logger):
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

    @mock.patch('paypal.subscriptions.logger')
    @mock.patch('paypal.subscriptions.requests.get')
    @mock.patch('paypal.subscriptions.construct_paypal_auth_headers')
    def test_get_subscription_success(self, mock_construct_headers, mock_get, mock_logger):
        # Mock construct_paypal_auth_headers
        mock_construct_headers.return_value = {
            "Authorization": "Bearer sample_token",
            "Content-Type": "application/json",
        }

        # Mock successful API response
        mock_response = mock.Mock()
        mock_response.json.return_value = {'status': 'ACTIVE'}
        mock_get.return_value = mock_response

        # Call function
        result = get_subscription(paypal_subscription_id='sub12345')

        # Validate result
        self.assertEqual(result, {'status': 'ACTIVE'})

    @mock.patch('paypal.subscriptions.logger')
    @mock.patch('paypal.subscriptions.requests.get')
    @mock.patch('paypal.subscriptions.construct_paypal_auth_headers')
    def test_get_subscription_failure(self, mock_construct_headers, mock_get, mock_logger):
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
            get_subscription(paypal_subscription_id='sub12345')

        # Check if logger.exception has been called
        mock_logger.exception.assert_called()