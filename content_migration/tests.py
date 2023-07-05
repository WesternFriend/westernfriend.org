from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch
from django.test import SimpleTestCase, TestCase
from wagtail.images.models import Image

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
        self.assertEqual(str(raw_book), "Test Book")
        self.assertEqual(raw_book.drupal_node_id, 123)
        self.assertEqual(raw_book.drupal_path, "/test-book")
        self.assertEqual(raw_book.drupal_body_migrated, "This is a test book.")
        self.assertEqual(raw_book.description, "This is a test book.")
        self.assertEqual(raw_book.image_url, "https://example.com/test-book.jpg")
        self.assertEqual(raw_book.price, Decimal("19.99"))
        self.assertEqual(raw_book.authors, [1, 2, 3])

    @patch("content_migration.models.get_or_create_image")
    def test_to_book(
        self,
        mock_get_or_create_image: Mock,
    ) -> None:
        # Given
        title = "Test Title"
        drupal_node_id = 123
        drupal_path = "/test/path"
        drupal_body_migrated = "Test body"
        description = "Test description"
        image_url = "https://example.com/image.jpg"
        price = Decimal("10.00")
        authors = [1, 2, 3]

        raw_book = RawBook(
            title=title,
            drupal_node_id=drupal_node_id,
            drupal_path=drupal_path,
            drupal_body_migrated=drupal_body_migrated,
            description=description,
            image_url=image_url,
            price=price,
            authors=authors,
        )

        # Mock Image
        file_name = "image.png"
        mock_image = MagicMock(spec=Image, title=file_name)
        mock_image._state = Mock(db="default")

        mock_get_or_create_image.return_value = mock_image

        book = raw_book.to_book()

        # Then
        mock_get_or_create_image.assert_called_once_with(image_url=image_url)
        assert book.title == title
        assert book.drupal_node_id == drupal_node_id
        assert book.drupal_path == drupal_path
        assert book.drupal_body_migrated == drupal_body_migrated
        assert book.description == description
        assert book.price == price
        assert book.image == mock_image

    @patch("content_migration.models.get_or_create_image")
    def test_get_or_create_image(
        self,
        mock_get_or_create_image: Mock,
    ) -> None:
        # Given
        image_url = "https://example.com/image.jpg"
        raw_book = RawBook(
            title="Test Title",
            drupal_node_id=123,
            drupal_path="/test/path",
            drupal_body_migrated="Test body",
            description="Test description",
            image_url=image_url,
            price=Decimal(10.00),
            authors=[1, 2, 3],
        )

        # When
        raw_book.get_or_create_image()

        # Then
        mock_get_or_create_image.assert_called_once_with(
            image_url=image_url,
        )


class TestCentsToDollars(SimpleTestCase):
    def test_cents_to_dollars(self) -> None:
        self.assertEqual(cents_to_dollars("1000"), Decimal("10.00"))
        self.assertEqual(cents_to_dollars("1999"), Decimal("19.99"))

    def test_cents_to_dollars_with_invalid_input(self) -> None:
        with self.assertRaises(TypeError):
            cents_to_dollars("abc")
