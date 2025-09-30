from django.core.management.base import BaseCommand

from library.factories import LibraryItemFactory
from library.models import LibraryIndexPage


class Command(BaseCommand):
    help = "Generate random library items"

    def handle(self, *args: tuple, **options: dict) -> None:
        self.stdout.write("Creating random library items...")

        number_of_library_items = 100

        library_item_index_page = LibraryIndexPage.objects.first()

        for _ in range(number_of_library_items):
            # create a new library item
            library_item = (
                LibraryItemFactory.build()
            )  # we use .build() here to prepare the object without saving it
            library_item_index_page.add_child(
                instance=library_item,
            )  # the parent.add_child() method will handle the path and depth fields
            library_item.save_revision().publish()

        self.stdout.write(self.style.SUCCESS("Successfully created library items"))
