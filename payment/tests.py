from django.conf import settings
from django.test import TestCase

from django.test import Client
from django.urls import reverse
from orders.factories import OrderFactory

from orders.models import Order


class TestProcessBookstoreOrderPayment(TestCase):
    def setUp(self):
        self.client = Client()
        self.order: Order = OrderFactory()  # type: ignore

    def test_process_bookstore_order_payment(self):
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



class TestPaymentViews(TestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_payment_done_view(self) -> None:
        response = self.client.get(reverse("payment:done"))
        self.assertEqual(response.status_code, 200)

    def test_payment_canceled_view(self) -> None:
        response = self.client.get(reverse("payment:canceled"))
        self.assertEqual(response.status_code, 200)
