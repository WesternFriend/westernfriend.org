from django.test import TestCase
from .factories import OrderFactory


class OrderModelTest(TestCase):
    def test_purchaser_full_name(self) -> None:
        # Create an Order instance using the factory
        order = OrderFactory(
            purchaser_given_name="John",
            purchaser_family_name="Doe",
            purchaser_meeting_or_organization="Western Friend",
        )

        # Test the method
        self.assertEqual(order.purchaser_full_name, "John Doe Western Friend")

        # Test with empty purchaser_family_name
        order.purchaser_family_name = ""
        order.save()
        self.assertEqual(order.purchaser_full_name, "John Western Friend")

        # Test with only purchaser_meeting_or_organization
        order.purchaser_given_name = ""
        order.save()
        self.assertEqual(order.purchaser_full_name, "Western Friend")
