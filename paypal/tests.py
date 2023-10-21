from unittest import mock
from django.test import TestCase
from requests.exceptions import HTTPError


from .orders import (
    create_order,
    capture_order,
)
from .subscriptions import (
    get_subscription,
    subscription_is_active,
)
from .utils import (
    PayPalError,
    get_auth_token,
    construct_paypal_auth_headers,
)


class GetAuthTokenTest(TestCase):
    @mock.patch("paypal.paypal.requests.post")
    def test_get_auth_token_success(self, mock_post):
        # Mock successful API response
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "some_token"}
        mock_post.return_value = mock_response

        # Test function
        result = get_auth_token()
        self.assertEqual(result, "some_token")

    @mock.patch("paypal.paypal.requests.post")
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

    @mock.patch('paypal.paypal.get_auth_token')
    def test_construct_paypal_auth_headers(self, mock_get_auth_token):
        # Mock get_auth_token to return a sample token
        mock_get_auth_token.return_value = 'sample_token'

        # Call the function and get the result
        result = construct_paypal_auth_headers()

        # Validate the result
        expected_result = {
            "Authorization": "Bearer sample_token",
            "Content-Type": "application/json",
        }
        self.assertEqual(result, expected_result)