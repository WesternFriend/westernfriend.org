from decimal import Decimal
from unittest.mock import Mock, patch
from django.test import RequestFactory, TestCase
from django.template.response import TemplateResponse
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse
from wagtail.models import Page
from cart.views import cart_detail
from content_migration.management.shared import get_or_create_site_root_page

from store.factories import ProductFactory

from .cart import Cart
from store.models import Product, ProductIndexPage, StoreIndexPage


def scaffold_product_index_page() -> ProductIndexPage:
    # Create a parent page
    root_page = get_or_create_site_root_page()
    # create the store index page
    store_index_page = StoreIndexPage(
        title="Bookstore",
        show_in_menus=True,
    )
    root_page.add_child(instance=store_index_page)

    # create the product index page
    product_index_page = ProductIndexPage(
        title="Products",
    )
    store_index_page.add_child(instance=product_index_page)

    return product_index_page


class CartTestCase(TestCase):
    def setUp(self) -> None:
        self.request = RequestFactory().get("/")

        # Add session middleware to the request
        middleware = SessionMiddleware(Mock())
        middleware.process_request(self.request)
        self.request.session.save()

        product_index_page = scaffold_product_index_page()

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
        self.assertEqual(len(cart), 2)
        self.assertEqual(cart.get_subtotal_price(), Decimal("19.98"))

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

    def test_get_subtotal_price_with_quantity_two(self) -> None:
        cart = Cart(self.request)

        cart.add(self.product1, quantity=2)

        subtotal_price = cart.get_subtotal_price()

        self.assertEqual(subtotal_price, Decimal("19.98"))

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


class CartDetailViewTest(TestCase):
    def setUp(self) -> None:
        self.request_factory = RequestFactory()

        product_index_page = scaffold_product_index_page()

        # create some test products using the ProductFactory
        self.product1 = ProductFactory.build()
        self.product2 = ProductFactory.build()

        product_index_page.add_child(instance=self.product1)
        product_index_page.add_child(instance=self.product2)

    def test_cart_detail_view(self) -> None:
        # make sure request has session middleware
        request = self.request_factory.get("/")
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        request.session.save()

        # add products to the cart
        cart = Cart(request)

        product_two_quantity = 2
        cart.add(self.product1)
        cart.add(self.product2, quantity=product_two_quantity)

        # get the response
        response = cart_detail(request)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, TemplateResponse)
        self.assertEqual(response.template_name, "cart/detail.html")
        self.assertIn("cart", response.context_data)  # type: ignore

        cart_items = list(response.context_data["cart"])  # type: ignore
        expected_cart_length = 2
        self.assertEqual(len(cart_items), expected_cart_length)

        default_cart_quantity = 1
        self.assertEqual(
            cart_items[0]["product"],
            self.product1,
        )
        self.assertEqual(
            cart_items[0]["quantity"],
            default_cart_quantity,
        )
        self.assertEqual(
            cart_items[0]["price"],
            self.product1.price,
        )
        expected_total_price_item_one = (
            cart_items[0]["price"] * cart_items[0]["quantity"]
        )
        self.assertEqual(
            cart_items[0]["total_price"],
            expected_total_price_item_one,
        )

        self.assertEqual(
            cart_items[1]["product"],
            self.product2,
        )
        self.assertEqual(
            cart_items[1]["quantity"],
            product_two_quantity,
        )
        self.assertEqual(
            cart_items[1]["price"],
            self.product2.price,
        )
        expected_total_price_item_two = (
            cart_items[1]["price"] * cart_items[1]["quantity"]
        )
        self.assertEqual(
            cart_items[1]["total_price"],
            expected_total_price_item_two,
        )

    def test_cart_add_view(self) -> None:
        # use Django TestClient.client to make a POST request to the
        # cart:add URL using reverse("cart:add") to get the URL
        # and passing in the product id as a keyword argument
        # with context containing a quantity of 1
        # and follow=True to follow redirects

        # Make sure initial cart is empty
        cart = Cart(self.client)  # type: ignore
        self.assertEqual(len(cart), 0)
        self.assertNotIn(self.product1, cart.get_cart_products())

        # Add product to cart
        response = self.client.post(
            reverse(
                "cart:add",
                kwargs={"product_id": self.product1.id},
            ),
            {"quantity": 1},
            follow=True,
        )
        # Make sure request was successful
        self.assertEqual(response.status_code, 200)

        # check that the redirect goes to the cart:detail URL
        self.assertEqual(
            response.redirect_chain[0][0],
            reverse("cart:detail"),
        )

        # check that the product was added to the cart
        cart = Cart(self.client)  # type: ignore
        self.assertEqual(len(cart), 1)
        self.assertIn(self.product1, cart.get_cart_products())

    def test_cart_remove_view(self) -> None:
        # Make an initial cart with a single product
        cart = Cart(self.client)  # type: ignore
        cart.add(self.product1)

        # assert that cart contains product
        self.assertEqual(len(cart), 1)
        self.assertIn(self.product1, cart.get_cart_products())

        # Make a POST request to the cart:remove URL
        # using reverse("cart:remove") to get the URL
        # and passing in the product id as a keyword argument
        response = self.client.post(
            reverse(
                "cart:remove",
                kwargs={"product_id": self.product1.id},
            ),
            follow=True,
        )

        # Make sure request was successful
        self.assertEqual(response.status_code, 200)

        # check that the redirect goes to the cart:detail URL
        self.assertEqual(
            response.redirect_chain[0][0],
            reverse("cart:detail"),
        )

        # check that the product was removed from the cart
        cart = Cart(self.client)  # type: ignore
        self.assertEqual(len(cart), 0)
        self.assertNotIn(self.product1, cart.get_cart_products())

    def tearDown(self) -> None:
        # delete all pages
        Page.objects.all().delete()

        return super().tearDown()
