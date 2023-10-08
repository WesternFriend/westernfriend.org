from django.urls import path
from . import views

app_name = "paypal"

urlpatterns = [
    path(
        "create_order/",
        views.create_paypal_order,
        name="create_paypal_order",
    ),
    path(
        "capture_order/",
        views.capture_paypal_order,
        name="capture_paypal_order",
    ),
]
