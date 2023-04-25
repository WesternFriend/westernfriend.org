from django.shortcuts import redirect, render, reverse

from cart.cart import Cart

from .forms import OrderCreateForm
from .models import OrderItem


def order_create(request):
    cart = Cart(request)

    if request.method == "POST":
        # Create copy of cart,
        # so we can modify shipping cost
        cart_order = request.POST.copy()

        # Calculate shipping cost, to prevent users from changing value
        cart_order["shipping_cost"] = cart.get_shipping_cost()

        # Instantiate form with updated cart order (incl. shipping cost)
        form = OrderCreateForm(cart_order)

        if form.is_valid():
            order = form.save()

            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product_title=item["product_title"],
                    product_id=item["product_id"],
                    price=item["price"],
                    quantity=item["quantity"],
                )

            cart.clear()

            # set the order in the session
            request.session["order_id"] = order.id

            # redirect for payment
            return redirect(
                reverse("payment:process", kwargs={"previous_page": "bookstore_order"})
            )

    else:
        form = OrderCreateForm()

        return render(
            request,
            template_name="orders/create.html",
            context={"cart": cart, "form": form},
        )
