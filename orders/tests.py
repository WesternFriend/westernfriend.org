from django.test import TestCase
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
    @classmethod
    def setUpTestData(cls) -> None:
        # Create an OrderItem instance using the factory
        cls.order_item = OrderItem(
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
