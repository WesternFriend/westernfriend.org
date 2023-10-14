import logging

from django.conf import settings


from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from orders.models import Order



paypal_client_id = settings.PAYPAL_CLIENT_ID

logger = logging.getLogger(__name__)



def render_payment_processing_page(
    request: HttpRequest,
    order: Order,
) -> HttpResponse:
    """Render the payment processing page."""

    return render(
        request,
        "payment/process.html",
        {
            "paypal_client_id": paypal_client_id,
            "order": order,
        },
    )

def process_bookstore_order_payment(
    request: HttpRequest,
    order_id: int,
) -> HttpResponse:
    """Process a payment for a bookstore order."""

    order = get_object_or_404(Order, id=order_id)

    return render_payment_processing_page(
        request=request,
        order=order,
    )


def payment_done(
    request: HttpRequest,
) -> HttpResponse:
    return render(request, "payment/done.html")


def payment_canceled(
    request: HttpRequest,
) -> HttpResponse:
    return render(request, "payment/canceled.html")
