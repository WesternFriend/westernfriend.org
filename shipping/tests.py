from decimal import Decimal
from django.test import SimpleTestCase
from .calculator import get_book_shipping_cost


class BookShippingTest(SimpleTestCase):
    """Test the book shipping cost calculator."""

    def test_book_shipping_cost(self) -> None:
        # define a mapping of book_quantity to expected shipping_cost
        quantity_cost_expectations = {
            # book_quantity >= 16 = 0 * book_quantity = 0
            16: Decimal("0.00"),
            # range(11, 16) = 1 * book_quantity´
            15: Decimal("15.00"),
            14: Decimal("14.00"),
            13: Decimal("13.00"),
            12: Decimal("12.00"),
            11: Decimal("11.00"),
            # range(5, 11) = 2 * book_quantity
            10: Decimal("20.00"),
            9: Decimal("18.00"),
            8: Decimal("16.00"),
            7: Decimal("14.00"),
            6: Decimal("12.00"),
            5: Decimal("10.00"),
            # range(2, 5) = 3 * book_quantity
            4: Decimal("12.00"),
            3: Decimal("9.00"),
            2: Decimal("6.00"),
            # < 2 = 4 * book_quantity
            1: Decimal("4.00"),
        }

        # loop over the mapping and test each case
        for book_quantity, expected_shipping_cost in quantity_cost_expectations.items():
            with self.subTest(book_quantity=book_quantity):
                self.assertEqual(
                    get_book_shipping_cost(book_quantity), expected_shipping_cost
                )
