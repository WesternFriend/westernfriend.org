import time

from django.test import TestCase
from django.urls import reverse
from wagtail.models import Page
from wagtail.search.backends import get_search_backend


class SearchPerformanceTestCase(TestCase):
    def setUp(self) -> None:
        # Create some test pages
        root_page = Page.objects.first()

        # Create test pages (we'll create just a few for testing)
        for i in range(10):
            title = f"Test Page {i}"
            test_page = Page(title=title)
            root_page.add_child(instance=test_page)
            test_page.save()

        # Index the pages
        search_backend = get_search_backend()
        search_backend.reset_index()
        search_backend.add_bulk(Page.objects.all())

    def test_search_performance(self) -> None:
        """Test the performance of the search view"""
        # Record the start time
        start_time = time.time()

        # Perform the search
        response = self.client.get(
            reverse("search"),
            {"query": "Test"},
        )

        # Calculate the elapsed time
        elapsed_time = time.time() - start_time

        # Check that the search completes in a reasonable time
        # This is a simple benchmark; adjust as needed
        self.assertLess(elapsed_time, 1.0)  # Should complete in less than 1 second
        self.assertEqual(response.status_code, 200)

        # Test that caching works by performing the search again
        start_time = time.time()
        response = self.client.get(
            reverse("search"),
            {"query": "Test"},
        )
        elapsed_time = time.time() - start_time

        # Second search should be faster due to caching
        self.assertLess(elapsed_time, 0.5)  # Should be faster the second time
        self.assertEqual(response.status_code, 200)
