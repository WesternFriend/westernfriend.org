from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST, require_GET

from store.models import Product

from .cart import Cart
from .forms import CartAddProductForm


@require_POST
def cart_add(
    request: HttpRequest,
    product_id: int,
) -> HttpResponse:
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)

    if form.is_valid():
        form_clean = form.cleaned_data

        cart.add(
            product=product,
            quantity=form_clean["quantity"],
            update_quantity=form_clean["update"],
        )

    return redirect("cart:detail")


@require_POST
def cart_remove(
    request: HttpRequest,
    product_id: int,
) -> HttpResponse:
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    cart.remove(product)

    return redirect("cart:detail")


@require_GET
def cart_detail(
    request: HttpRequest,
) -> TemplateResponse:
    cart = Cart(request)

    for item in cart:
        item["update_quantity_form"] = CartAddProductForm(
            initial={
                "quantity": item["quantity"],
                "update": True,
            }
        )

    context = {
        "cart": cart,
    }

    return TemplateResponse(
        request,
        "cart/detail.html",
        context,
    )
