from decimal import Decimal
from unittest.mock import Mock, patch
from django.test import RequestFactory, TestCase
from django.contrib.sessions.middleware import SessionMiddleware
from wagtail.models import Page

from .cart import Cart
from home.models import HomePage
from store.models import Product, ProductIndexPage, StoreIndexPage


class CartTestCase(TestCase):
    def setUp(self) -> None:
        self.request = RequestFactory().get("/")

        # Add session middleware to the request
        middleware = SessionMiddleware(Mock())
        middleware.process_request(self.request)
        self.request.session.save()

        # get Site Root
        root_page = Page.objects.get(id=1)

        # Create HomePage
        home_page = HomePage(
            title="Welcome",
        )

        root_page.add_child(instance=home_page)
        # root_page.save()

        # Create StoreIndexPage
        store_index_page = StoreIndexPage(
            title="Bookstore",
            show_in_menus=True,
        )
        home_page.add_child(instance=store_index_page)

        # Create ProductIndexPage
        product_index_page = ProductIndexPage(
            title="Products",
        )
        store_index_page.add_child(instance=product_index_page)

        self.product1 = Product(
            title="Product 1",
            price=Decimal("9.99"),
        )
        self.product2 = Product(
            title="Product 2",
            price=Decimal("19.99"),
        )
        product_index_page.add_child(instance=self.product1)
        product_index_page.add_child(instance=self.product2)

    def test_cart_initialization(self) -> None:
        cart = Cart(self.request)

        self.assertEqual(len(cart), 0)
        self.assertEqual(cart.get_subtotal_price(), Decimal("0"))

    def test_add_product(self) -> None:
        cart = Cart(self.request)

        cart.add(self.product1)
        self.assertEqual(len(cart), 1)
        self.assertEqual(cart.get_subtotal_price(), Decimal("9.99"))

        cart.add(self.product1, quantity=2)
        self.assertEqual(len(cart), 3)
        self.assertEqual(cart.get_subtotal_price(), Decimal("29.97"))

    def test_save_cart(self) -> None:
        cart = Cart(self.request)
        cart.save()

        self.assertTrue(cart.session.modified)

    def test_remove_product(self) -> None:
        cart = Cart(self.request)

        cart.add(self.product1)

        self.assertEqual(len(cart), 1)
        cart.remove(self.product1)
        self.assertEqual(len(cart), 0)

    def test_get_cart_products(self) -> None:
        cart = Cart(self.request)

        cart.add(self.product1)
        cart.add(self.product2)

        cart_products = cart.get_cart_products()

        self.assertEqual(len(cart_products), 2)
        self.assertIn(self.product1, cart_products)
        self.assertIn(self.product2, cart_products)

    def test_get_subtotal_price(self) -> None:
        cart = Cart(self.request)

        cart.add(self.product1)
        cart.add(self.product2, quantity=2)

        subtotal_price = cart.get_subtotal_price()

        self.assertEqual(subtotal_price, Decimal("49.97"))

    def test_get_shipping_cost(self) -> None:
        cart = Cart(self.request)

        # Mocking the get_shipping_cost method
        expected_shipping_cost = Decimal("10.00")
        with patch.object(
            cart,
            "get_shipping_cost",
            return_value=expected_shipping_cost,
        ):
            shipping_cost = cart.get_shipping_cost()

        self.assertEqual(shipping_cost, expected_shipping_cost)

    def test_cart_iteration(self) -> None:
        cart = Cart(self.request)

        cart.add(self.product1)
        cart.add(self.product2, quantity=2)

        cart_items = list(cart)

        self.assertEqual(len(cart_items), 2)
        self.assertEqual(cart_items[0]["product"], self.product1)
        self.assertEqual(cart_items[0]["quantity"], 1)
        self.assertEqual(cart_items[0]["price"], Decimal("9.99"))
        self.assertEqual(cart_items[0]["total_price"], Decimal("9.99"))

        self.assertEqual(cart_items[1]["product"], self.product2)
        self.assertEqual(cart_items[1]["quantity"], 2)
        self.assertEqual(cart_items[1]["price"], Decimal("19.99"))
        self.assertEqual(cart_items[1]["total_price"], Decimal("39.98"))

    def tearDown(self) -> None:
        # delete all pages
        Page.objects.all().delete()

        return super().tearDown()
