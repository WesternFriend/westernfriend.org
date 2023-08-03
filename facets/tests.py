from django.test import TestCase

from facets.models import FacetIndexPage
from library.models import LibraryIndexPage
from .factories import (
    FacetIndexPageFactory,
)


class TestFacetIndexPage(TestCase):
    def test_facet_index_page_creation(self) -> None:
        """Test that a FacetIndexPage can be created."""
        facet_index_page = FacetIndexPageFactory.create()
        self.assertIsNotNone(facet_index_page)
        self.assertIsInstance(
            facet_index_page,
            FacetIndexPage,
        )

        self.assertIsInstance(
            facet_index_page.get_parent().specific,
            LibraryIndexPage,
        )
