from dataclasses import dataclass
from decimal import Decimal

from wagtail.images.models import Image

from store.models import Book

from content_migration.management.shared import get_or_create_image


@dataclass
class RawBook:
    title: str
    drupal_node_id: int
    drupal_path: str
    drupal_body_migrated: str
    description: str
    image_url: str
    price: Decimal
    authors: list[int]

    def __str__(self) -> str:
        return self.title

    @classmethod
    def from_csv_row(
        cls,
        row: dict,
    ) -> "RawBook":
        return cls(
            title=row["title"],
            drupal_node_id=row["node_id"],
            drupal_path=row["url_path"],
            drupal_body_migrated=row["description"],
            description=row["description"],
            image_url=row["cover_image"],
            # row price is in cents, so divide by 100 to get dollars
            price=Decimal(row["price"]) / 100,
            authors=[int(author_id) for author_id in row["authors"].split(",")],
        )

    def get_or_create_image(self) -> Image:
        return get_or_create_image(
            image_url=self.image_url,
        )

    def to_book(self) -> Book:
        return Book(
            title=self.title,
            drupal_node_id=self.drupal_node_id,
            drupal_path=self.drupal_path,
            drupal_body_migrated=self.drupal_body_migrated,
            description=self.description,
            price=self.price,
            image=self.get_or_create_image(),
        )
