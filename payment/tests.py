from django.conf import settings
from django.test import TestCase
from unittest.mock import MagicMock, Mock, patch
from django.http import HttpRequest

from django.test import Client
from django.urls import reverse
from orders.factories import OrderFactory

from orders.models import Order

from .views import (
    render_payment_processing_page,
    process_bookstore_order_payment,
)


class TestPaymentProcessingPage(TestCase):
    def setUp(self):
        self.client = Client()
        self.order: Order = OrderFactory()  # type: ignore

    def test_render_payment_processing_page(self):
        paypal_client_id = settings.PAYPAL_CLIENT_ID
        url = reverse(
            "payment:process_bookstore_order_payment",
            kwargs={
                "order_id": self.order.id,
            },
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "payment/process.html")
        self.assertEqual(
            response.context["order"],
            self.order,
        )
        self.assertEqual(
            response.context["paypal_client_id"],
            paypal_client_id,
        )


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
