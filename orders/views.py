from django.contrib import messages
from django.db import transaction
from django.http import HttpRequest, HttpResponse, QueryDict
from django.shortcuts import redirect, render
from django.urls import reverse

from cart.cart import Cart
from orders.forms import OrderCreateForm

from .models import Order, OrderItem


def create_cart_order_items(
    order: Order,
    cart: Cart,
) -> None:
    """Create OrderItems from Cart items.

    The price comes from the Product row, not from the cart session,
    so a price changed after the product was added to the cart is
    the one the order records.
    """

    for item in cart:
        OrderItem.objects.create(
            order=order,
            product_title=item["product_title"],
            product_id=item["product_id"],
            price=item["product"].price,
            quantity=item["quantity"],
        )


def order_create(request: HttpRequest) -> HttpResponse:
    """Create an Order from the Cart."""
    cart = Cart(request)

    if not cart:
        messages.info(request, "Your cart is empty. Add an item before checking out.")
        return redirect("cart:detail")

    if request.method == "POST":
        # Create copy of cart,
        # so we can modify shipping cost
        cart_order: QueryDict = request.POST.copy()

        # Calculate shipping cost, to prevent users from changing value
        cart_order["shipping_cost"] = str(cart.get_shipping_cost())

        # Instantiate form with updated cart order (incl. shipping cost)
        form = OrderCreateForm(cart_order)

        if form.is_valid():
            with transaction.atomic():
                order = form.save()
                create_cart_order_items(order, cart)

            # The order is committed, so the cart has done its job. Clearing
            # it here, not inside the transaction, keeps the cart if the
            # order fails to save, so the purchaser can try again.
            cart.clear()

            return redirect(
                reverse(
                    "payment:process_bookstore_order_payment",
                    kwargs={
                        "order_id": order.id,
                    },
                ),
            )
        return render(
            request,
            template_name="orders/create.html",
            context={
                "cart": cart,
                "form": form,
            },
        )

    form = OrderCreateForm()

    return render(
        request,
        template_name="orders/create.html",
        context={
            "cart": cart,
            "form": form,
        },
    )
