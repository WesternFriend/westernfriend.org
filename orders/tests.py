from unittest.mock import MagicMock, patch
from django.test import Client, TestCase
from django.urls import reverse


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
        expected_cost = 39.98

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
