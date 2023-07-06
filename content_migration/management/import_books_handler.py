import csv

from tqdm import tqdm
from content_migration.management.shared import get_or_create_book_author

from content_migration.models import RawBook
from store.models import Book, ProductIndexPage


def handle_import_books(file_name: str) -> None:
    product_index_page = ProductIndexPage.objects.get()

    with open(file_name) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in tqdm(
            reader,
            desc="Books",
            unit="book",
        ):
            raw_book = RawBook.from_csv_row(row=row)

            book_exists = Book.objects.filter(
                drupal_node_id=raw_book.drupal_node_id,
            ).exists()

            if book_exists:
                book = Book.objects.get(
                    drupal_node_id=raw_book.drupal_node_id,
                )

                book.title = raw_book.title
                book.description = raw_book.description
                book.price = raw_book.price
                book.image = raw_book.get_or_create_image()

                book.authors.clear()

                book.save()
            else:
                book = raw_book.to_book()

                product_index_page.add_child(instance=book)

                product_index_page.save()

            for drupal_author_id in raw_book.authors:
                # ensure book author exists
                _ = get_or_create_book_author(
                    book=book,
                    drupal_author_id=drupal_author_id,
                )
