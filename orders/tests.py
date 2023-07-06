from django.test import TestCase
from .factories import OrderFactory


class OrderModelTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        # Create an Order instance using the factory
        cls.order = OrderFactory(
            id=1,
            purchaser_given_name="John",
            purchaser_family_name="Doe",
            purchaser_meeting_or_organization="Western Friend",
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
