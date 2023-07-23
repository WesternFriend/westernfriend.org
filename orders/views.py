from django.http import HttpRequest, HttpResponse, QueryDict
from django.shortcuts import redirect, render
from django.urls import reverse

from cart.cart import Cart

from .models import Order, OrderItem


def create_cart_order_items(
    order: Order,
    cart: Cart,
) -> None:
    for item in cart:
        OrderItem.objects.create(
            order=order,
            product_title=item["product_title"],
            product_id=item["product_id"],
            price=item["price"],
            quantity=item["quantity"],
        )


def order_create(request: HttpRequest) -> HttpResponse:
    # Avoid circular import
    from .forms import OrderCreateForm

    cart = Cart(request)

    if request.method == "POST":
        # Create copy of cart,
        # so we can modify shipping cost
        cart_order: QueryDict = request.POST.copy()

        # Calculate shipping cost, to prevent users from changing value
        cart_order["shipping_cost"] = str(cart.get_shipping_cost())

        # Instantiate form with updated cart order (incl. shipping cost)
        form = OrderCreateForm(cart_order)

        if form.is_valid():
            order = form.save()

            create_cart_order_items(order, cart)

            # TODO: consider moving this to the payment app
            # so it can be cleared after successful payment.
            # That way, the user can retry checkout if payment fails.
            cart.clear()

            # redirect for payment
            return redirect(
                reverse(
                    "payment:process_bookstore_order_payment",
                    kwargs={
                        "order_id": order.id,
                    },
                ),
            )
        else:
            return render(
                request,
                template_name="orders/create.html",
                context={
                    "cart": cart,
                    "form": form,
                },
            )

    else:
        form = OrderCreateForm()

        return render(
            request,
            template_name="orders/create.html",
            context={
                "cart": cart,
                "form": form,
            },
        )
