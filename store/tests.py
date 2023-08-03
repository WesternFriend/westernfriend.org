from django.test import TestCase

from home.models import HomePage
from store.models import Product, ProductIndexPage, StoreIndexPage
from .factories import (
    StoreIndexPageFactory,
    ProductIndexPageFactory,
    ProductFactory,
)


class TestStoreIndexPageFactory(TestCase):
    def test_store_index_page_factory(self) -> None:
        """Test that a Topic can be created."""
        store_index_page = StoreIndexPageFactory.create()

        self.assertIsInstance(
            store_index_page,
            StoreIndexPage,
        )

        self.assertIsInstance(
            store_index_page.get_parent().specific,
            HomePage,
        )


class TestProductIndexPageFactory(TestCase):
    def test_product_index_page_factory(self) -> None:
        """Test that a Topic can be created."""
        product_index_page = ProductIndexPageFactory.create()

        self.assertIsInstance(
            product_index_page,
            ProductIndexPage,
        )

        self.assertIsInstance(
            product_index_page.get_parent().specific,
            StoreIndexPage,
        )


class TestProductFactory(TestCase):
    def test_product_factory(self) -> None:
        """Test that a Topic can be created."""
        product = ProductFactory.create()

        self.assertIsInstance(
            product,
            Product,
        )

        self.assertIsInstance(
            product.get_parent().specific,
            ProductIndexPage,
        )
