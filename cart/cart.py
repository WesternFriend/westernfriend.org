from decimal import Decimal
from collections.abc import Generator

from django.conf import settings
from django.http import HttpRequest

from shipping.calculator import get_book_shipping_cost
from store.models import Product


class Cart:
    def __init__(self, request: HttpRequest) -> None:
        """Initialize the cart."""
        self.session = request.session

        cart = self.session.get(settings.CART_SESSION_ID)

        if not cart:
            # save an empty cart in the session
            cart = self.session[settings.CART_SESSION_ID] = {}

        self.cart = cart

    def add(
        self,
        product: Product,
        quantity: int = 1,
    ) -> None:
        """Add a product to the cart or update its quantity."""
        product_id = str(product.id)  # type: ignore

        self.cart[product_id] = {
            "product_title": product.title,
            "product_id": product_id,
            "quantity": quantity,
            "price": str(product.price),
        }

        self.save()

    def save(self) -> None:
        # mark the session as "modified"
        # to make sure it gets saved

        self.session.modified = True

    def remove(self, product: Product) -> None:
        """Remove a product from the cart."""
        product_id = str(product.id)  # type: ignore

        if product_id in self.cart:
            del self.cart[product_id]

            self.save()

    def get_cart_products(self) -> list[Product]:
        product_ids = self.cart.keys()

        # get the product objects and add them to the cart
        return Product.objects.filter(id__in=product_ids)

    def get_total_price(self) -> Decimal:
        int_sum = sum(
            [
                self.get_subtotal_price(),
                self.get_shipping_cost(),
            ],
        )
        return Decimal(int_sum).quantize(Decimal("0.01"))

    def get_subtotal_price(self) -> Decimal:
        totals = [
            Decimal(item["price"]) * item["quantity"] for item in self.cart.values()
        ]
        product_sum = sum(totals)
        return Decimal(product_sum).quantize(Decimal("0.01"))

    def get_shipping_cost(self) -> Decimal:
        book_quantity = sum(item["quantity"] for item in self.cart.values())

        return get_book_shipping_cost(book_quantity)

    def clear(self) -> None:
        # remove cart from session
        del self.session[settings.CART_SESSION_ID]

        self.save()

    def __iter__(self) -> Generator:
        """Get cart products from the database."""
        # get the product objects and add them to the cart
        products = self.get_cart_products()

        cart = self.cart.copy()

        for product in products:
            if str(product.id) not in cart:  # type: ignore
                continue

            cart[str(product.id)]["product"] = product  # type: ignore

        for item in cart.values():
            item["price"] = Decimal(item["price"])
            item["total_price"] = item["price"] * item["quantity"]

            yield item

    def __len__(self) -> int:
        """Count all items in the cart."""

        # TODO: determine whether this should count the number of products
        # or the total quantity of products
        item_quantities = [item["quantity"] for item in self.cart.values()]

        return sum(item_quantities)
