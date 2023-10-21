from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch
from django.http import HttpRequest

from django.test import Client, RequestFactory
from django.urls import reverse
from orders.factories import OrderFactory

from orders.models import Order

from .views import (
    render_payment_processing_page,
    process_bookstore_order_payment,
)


class TestPaymentProcessingPage(TestCase):
    @patch("braintree.ClientToken.generate")
    def test_render_payment_processing_page(self, mock_generate: Mock) -> None:
        # Mock Braintree token generator to return a fake token
        mock_generate.return_value = "fake_token"

        # Create a GET request with RequestFactory
        factory = RequestFactory()
        mock_request = factory.get("/fake-url")
        order: Order = OrderFactory()  # type: ignore

        # Execute function with mock request and arbitrary payment total
        response = render_payment_processing_page(mock_request, order)

        # Test if the response is 200 OK.
        self.assertEqual(response.status_code, 200)

        # Test if the correct context is used in the rendered template
        # by checking if the context variables are present in the response content.
        self.assertIn(b"fake_token", response.content)
        self.assertIn(b"100", response.content)


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


class TestPaymentViews(TestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_payment_done_view(self) -> None:
        response = self.client.get(reverse("payment:done"))
        self.assertEqual(response.status_code, 200)

    def test_payment_canceled_view(self) -> None:
        response = self.client.get(reverse("payment:canceled"))
        self.assertEqual(response.status_code, 200)
