from decimal import Decimal
from django.conf import settings
from shipping.calculator import get_book_shipping_cost
from store.models import Product

class Cart:
    def __init__(self, request):
        """Initialize the cart."""
        self.session = request.session
        cart_data = self.session.get(settings.CART_SESSION_ID)
        self.cart_data = cart_data if cart_data is not None else {}

        if not self.cart_data:
            # save an empty cart in the session
            self.cart_data = self.session[settings.CART_SESSION_ID] = {}

    def add(self, product, quantity=1, update_quantity=False):
        """Add a product to the cart or update its quantity."""
        product_id = str(product.id)
        if product_id not in self.cart_data:
            self.cart_data[product_id] = {
                "product_title": product.title,
                "product_id": product_id,
                "quantity": 0,
                "price": str(product.price),
            }
        if update_quantity:
            self.cart_data[product_id]["quantity"] = quantity
        else:
            self.cart_data[product_id]["quantity"] += quantity
        self.save()

    def save(self):
        # mark the session as "modified" to make sure it gets saved
        self.session.modified = True

    def remove(self, product):
        """Remove a product from the cart."""
        product_id = str(product.id)
        if product_id in self.cart_data:
            del self.cart_data[product_id]
            self.save()

    def get_cart_products(self):
        product_ids = self.cart_data.keys()
        # get the product objects and add them to the cart
        return Product.objects.filter(id__in=product_ids)

    def get_subtotal_price(self):
        return sum(
            Decimal(item["price"]) * item["quantity"] for item in self.cart_data.values()
        )

    def get_total_price(self):
        return sum([self.get_subtotal_price(), self.get_shipping_cost()])

    def get_shipping_cost(self):
        book_quantity = sum(item["quantity"] for item in self.cart_data.values())
        return get_book_shipping_cost(book_quantity)

    def clear(self):
        # remove cart from session
        del self.session[settings.CART_SESSION_ID]
        self.save()

    def __iter__(self):
        """Get cart products from the database."""
        # get the product objects and add them to the cart
        products = self.get_cart_products()
        cart_data = self.cart_data.copy()
        for product in products:
            cart_data[str(product.id)]["product"] = product
        for item in cart_data.values():
            item["price"] = Decimal(item["price"])
            item["total_price"] = item["price"] * item["quantity"]
            yield item

    def __len__(self):
        """Count all items in the cart."""
        item_quantities = [item["quantity"] for item in self.cart_data.values()]
        return sum(item_quantities)
