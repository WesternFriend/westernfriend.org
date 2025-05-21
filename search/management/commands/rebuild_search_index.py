from django.core.management.base import BaseCommand
from wagtail.models import Page
from wagtail.search.backends import get_search_backend


class Command(BaseCommand):
    help = "Rebuild the database search index"

    def handle(self, *args, **options):
        self.stdout.write("Rebuilding search index...")

        # Get the search backend
        search_backend = get_search_backend()

        # Remove stale entries
        self.stdout.write("Deleting stale entries...")
        search_backend.reset_index()

        # Add models with search_fields
        self.stdout.write("Adding pages to search index...")

        # Get all pages and index them in batches
        page_count = Page.objects.count()
        self.stdout.write(f"Adding {page_count} pages to search index...")

        # Use batching to prevent memory issues with large datasets
        batch_size = 100
        for i in range(0, page_count, batch_size):
            batch = Page.objects.all()[i : i + batch_size]
            search_backend.add_bulk(batch)
            self.stdout.write(f"Indexed pages {i} to {min(i + batch_size, page_count)}")

        self.stdout.write(self.style.SUCCESS("Successfully rebuilt search index."))
