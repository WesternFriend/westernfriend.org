from decimal import Decimal
from django.test import SimpleTestCase
from .calculator import get_book_shipping_cost


class BookShippingTest(SimpleTestCase):
    """Test the book shipping cost calculator."""

    def test_book_shipping_cost(self) -> None:
        # define a mapping of book_quantity to expected shipping_cost
        quantity_cost_expectations = {
            # 16 or more books shipping is free
            16: Decimal("0.00"),
            # 11 through 15 books, the shipping cost is 2 * book_quantity
            15: Decimal("30.00"),
            14: Decimal("28.00"),
            13: Decimal("26.00"),
            12: Decimal("24.00"),
            11: Decimal("22.00"),
            # 5 through 10 books, the shipping cost is 3 * book_quantity
            10: Decimal("30.00"),
            9: Decimal("27.00"),
            8: Decimal("24.00"),
            7: Decimal("21.00"),
            6: Decimal("18.00"),
            5: Decimal("15.00"),
            # 2 through 4 books, the shipping cost is 4 * book_quantity
            4: Decimal("16.00"),
            3: Decimal("12.00"),
            2: Decimal("8.00"),
            # for one book, the shipping cost is 5
            1: Decimal("5.00"),
        }

        # loop over the mapping and test each case
        for book_quantity, expected_shipping_cost in quantity_cost_expectations.items():
            with self.subTest(book_quantity=book_quantity):
                self.assertEqual(
                    get_book_shipping_cost(book_quantity),
                    expected_shipping_cost,
                )
