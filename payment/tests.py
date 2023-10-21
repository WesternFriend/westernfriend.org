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
    def test_render_payment_processing_page(self, mock_generate: Mock) -> None:
        assert False


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
