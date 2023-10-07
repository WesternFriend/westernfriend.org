from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from cart.cart import Cart
from cart.tests import scaffold_product_index_page

from orders.views import create_cart_order_items
from store.factories import ProductFactory


from .models import Order, OrderItem


class OrderModelTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        # Create an Order instance using the factory
        cls.order = Order(
            id=1,
            purchaser_given_name="John",
            purchaser_family_name="Doe",
            purchaser_meeting_or_organization="Western Friend",
            shipping_cost=4.00,
        )
        cls.order.save()

        # Create OrderItems
        cls.order_item_one = OrderItem.objects.create(
            order=cls.order,
            product_title="Product 1",
            product_id=1,
            price=10.00,
            quantity=2,
        )

        cls.order_item_two = OrderItem.objects.create(
            order=cls.order,
            product_title="Product 2",
            product_id=2,
            price=20.00,
            quantity=3,
        )

    def test_purchaser_full_name(self) -> None:
        # Test the method
        self.assertEqual(self.order.purchaser_full_name, "John Doe Western Friend")

        # Test with empty purchaser_family_name
        self.order.purchaser_family_name = ""
        self.order.save()
        self.assertEqual(self.order.purchaser_full_name, "John Western Friend")

        # Test with only purchaser_meeting_or_organization
        self.order.purchaser_given_name = ""
        self.order.save()
        self.assertEqual(self.order.purchaser_full_name, "Western Friend")

    def test_str_method(self) -> None:
        # Test the method
        self.assertEqual(
            str(self.order),
            "Order 1",
        )

    def test_order_get_total_cost(self):
        order_item_one_total = self.order_item_one.quantity * self.order_item_one.price
        order_item_two_total = self.order_item_two.quantity * self.order_item_two.price
        expected_total = order_item_one_total + order_item_two_total + self.order.shipping_cost
        expected_decimal = Decimal(expected_total).quantize(Decimal("0.01"))    
        self.assertEqual(self.order.get_total_cost(), expected_decimal)


class OrderItemModelTest(TestCase):
    def setUp(self) -> None:
        # Create an OrderItem instance using the factory
        self.order_item = OrderItem(
            id=1,
            product_title="Quaker Faith & Practice",
            product_id=1,
            price=19.99,
            quantity=2,
        )

    def test_str_method(self) -> None:
        expected_string = "2x Quaker Faith & Practice @ 19.99/each"

        self.assertEqual(
            str(self.order_item),
            expected_string,
        )

    def test_get_cost_method(self) -> None:
        expected_cost = Decimal("39.98")

        self.assertEqual(
            self.order_item.get_cost(),
            expected_cost,
        )


class OrderCreateViewTest(TestCase):
    def setUp(self) -> None:
        # Create a client to make requests
        self.client = Client()

        # Mock the Cart
        self.cart_mock = patch("cart.cart.Cart").start()

    def tearDown(self) -> None:
        # Stop the Cart mock
        patch.stopall()

    def test_order_create_view_get_request(self) -> None:
        # Send a GET request
        response = self.client.get(reverse("orders:order_create"))

        # Check that the response has a status code of 200
        self.assertEqual(response.status_code, 200)

        # Check if the correct template was used
        self.assertTemplateUsed(response, "orders/create.html")

    def test_order_create_view_post_request_form_valid(self) -> None:
        # Mock the OrderCreateForm
        with patch("orders.forms.OrderCreateForm") as MockOrderCreateForm:
            # Instance of the form
            mock_form = MagicMock()

            # Set is_valid to return True
            mock_form.is_valid.return_value = True

            # Set save to return a mock order with an id
            mock_order = MagicMock()
            mock_order.id = 1
            mock_form.save.return_value = mock_order

            # Set our mock form as the return value of the form class
            MockOrderCreateForm.return_value = mock_form

            # Send a POST request
            response = self.client.post(reverse("orders:order_create"))

            # Check that the response is a redirect
            self.assertEqual(response.status_code, 302)

            # Check if the redirect URL is correct
            self.assertRedirects(
                response,
                reverse(
                    "payment:process_bookstore_order_payment",
                    kwargs={"order_id": mock_order.id},
                ),
                fetch_redirect_response=False,
            )

    def test_order_create_view_post_request_form_invalid(self) -> None:
        # Create a dictionary with the invalid data you want to test
        invalid_data = {
            "field_name": "invalid value",
        }  # replace with your actual invalid data

        # Send a POST request using the client
        response = self.client.post(reverse("orders:order_create"), invalid_data)

        # Check that the response has a status code of 200
        self.assertEqual(response.status_code, 200)

        # Check if the correct template was used
        self.assertTemplateUsed(response, "orders/create.html")


class CreateCartOrderItemsTest(TestCase):
    def setUp(self) -> None:
        # Create an order instance
        self.order = Order.objects.create(
            purchaser_given_name="John",
            purchaser_family_name="Doe",
            purchaser_meeting_or_organization="Western Friend",
            shipping_cost=4.00,
        )

        # Create a request instance using RequestFactory
        self.factory = RequestFactory()
        self.request = self.factory.get("/")

        # Add session to request
        middleware = SessionMiddleware(Mock())
        middleware.process_request(self.request)
        self.request.session.save()

        # Create a cart instance
        self.cart = Cart(self.request)

        product_index_page = scaffold_product_index_page()

        # create some test products using the ProductFactory
        self.product1 = ProductFactory.build()
        self.product2 = ProductFactory.build()

        product_index_page.add_child(instance=self.product1)
        product_index_page.add_child(instance=self.product2)

        # Add products to the cart
        self.product1_quantity = 2
        self.product2_quantity = 3
        self.cart.add(
            self.product1,
            quantity=self.product1_quantity,
        )
        self.cart.add(
            self.product2,
            quantity=self.product2_quantity,
        )

    def test_create_cart_order_items(self) -> None:
        # Call the function with the order and cart
        create_cart_order_items(
            self.order,
            self.cart,
        )

        # Assert that the OrderItems were correctly created
        self.assertEqual(
            OrderItem.objects.count(),
            2,
        )
        item1 = OrderItem.objects.get(
            order=self.order,
            product_id=self.product1.id,
        )
        self.assertEqual(
            item1.product_title,
            self.product1.title,
        )
        self.assertEqual(
            item1.price,
            self.product1.price,
        )
        self.assertEqual(
            item1.quantity,
            self.product1_quantity,
        )

        item2 = OrderItem.objects.get(
            order=self.order,
            product_id=self.product2.id,
        )
        self.assertEqual(
            item2.product_title,
            self.product2.title,
        )
        self.assertEqual(
            item2.price,
            self.product2.price,
        )
        self.assertEqual(
            item2.quantity,
            self.product2_quantity,
        )
