from django.shortcuts import redirect, render, reverse
from .models import OrderItem
from .forms import OrderCreateForm
from cart.cart import Cart


def order_create(request):
    cart = Cart(request)

    if request.method == "POST":
        form = OrderCreateForm(request.POST)

        if form.is_valid():
            order = form.save()

            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    product_id=item["product_id"],
                    price=item["price"],
                    quantity=item["quantity"],
                )

            cart.clear()

            # set the order in the session
            request.session["order_id"] = order.id

            # redirect for payment
            return redirect(reverse("payment:process"))

    else:
        form = OrderCreateForm()

        return render(
            request,
            template_name="orders/create.html",
            context={"cart": cart, "form": form},
        )
