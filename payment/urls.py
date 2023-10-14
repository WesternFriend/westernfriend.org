from django.urls import path

from . import views

app_name = "payment"

urlpatterns = [
    path(
        "process/bookstore_order/<int:order_id>",
        views.process_bookstore_order_payment,
        name="process_bookstore_order_payment",
    ),
    path(
        "done/",
        views.payment_done,
        name="done",
    ),
    path(
        "canceled/",
        views.payment_canceled,
        name="canceled",
    ),
]
