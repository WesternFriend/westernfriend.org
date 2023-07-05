from decimal import Decimal
from django.test import SimpleTestCase, TestCase

from content_migration.models import RawBook, cents_to_dollars


class RawBookTest(TestCase):
    def test_from_csv_row(self) -> None:
        # Prepare the input
        row = {
            "title": "Test Book",
            "node_id": "123",
            "url_path": "/test-book",
            "description": "This is a test book.",
            "cover_image": "https://example.com/test-book.jpg",
            "price": "1999",  # price in cents
            "authors": "1,2,3",
        }

        # Call the method
        raw_book = RawBook.from_csv_row(row)

        # Check the result
        self.assertEqual(raw_book.title, "Test Book")
        self.assertEqual(raw_book.drupal_node_id, 123)
        self.assertEqual(raw_book.drupal_path, "/test-book")
        self.assertEqual(raw_book.drupal_body_migrated, "This is a test book.")
        self.assertEqual(raw_book.description, "This is a test book.")
        self.assertEqual(raw_book.image_url, "https://example.com/test-book.jpg")
        self.assertEqual(raw_book.price, Decimal("19.99"))
        self.assertEqual(raw_book.authors, [1, 2, 3])


class TestCentsToDollars(SimpleTestCase):
    def test_cents_to_dollars(self) -> None:
        self.assertEqual(cents_to_dollars("1000"), Decimal("10.00"))
        self.assertEqual(cents_to_dollars("1999"), Decimal("19.99"))

    def test_cents_to_dollars_with_invalid_input(self) -> None:
        with self.assertRaises(TypeError):
            cents_to_dollars("abc")
