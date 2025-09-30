from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST, require_GET

from store.models import Product, StoreIndexPage

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
        )

        cart.save()

    return redirect("cart:detail")


# Note: we allow GET requests here because we want to be able to
#       remove items from the cart by visiting a URL.
#       This is not a security issue because we are not changing
#       any data, only removing it from the session.
@require_GET
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
    store_index_page = StoreIndexPage.objects.first()

    for item in cart:
        item["update_quantity_form"] = CartAddProductForm(
            initial={
                "quantity": item["quantity"],
            },
        )

    context = {
        "cart": cart,
        "store_index_page": store_index_page,
    }

    return TemplateResponse(
        request,
        "cart/detail.html",
        context,
    )
