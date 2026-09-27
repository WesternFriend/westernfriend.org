from django.test import TestCase
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Site

from cart.forms import CartAddProductForm
from home.factories import HomePageFactory
from home.models import HomePage
from store.models import Product, ProductIndexPage, StoreIndexPage

from .factories import (
    BookFactory,
    ProductFactory,
    ProductIndexPageFactory,
    StoreIndexPageFactory,
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


class TestStoreIndexPageGetContext(TestCase):
    def test_store_index_page_get_context(self) -> None:
        """Test that a Topic can be created."""
        store_index_page = StoreIndexPageFactory.create()
        context = store_index_page.get_context(request=None)

        self.assertIn(
            "products",
            context,
        )

        self.assertIn(
            "cart_add_product_form",
            context,
        )
        self.assertIsInstance(
            context["cart_add_product_form"],
            CartAddProductForm,
        )


class TestProductIndexPageGetContext(TestCase):
    def test_product_index_page_get_context(self) -> None:
        """Test that ProductIndexPage.get_context includes live books."""
        product_index_page = ProductIndexPageFactory.create()
        book = BookFactory.create()
        context = product_index_page.get_context(request=None)

        self.assertIn(
            "books",
            context,
        )

        self.assertIn(
            book,
            context["books"],
        )

        self.assertIn(
            "cart_add_product_form",
            context,
        )
        self.assertIsInstance(
            context["cart_add_product_form"],
            CartAddProductForm,
        )


class TestProductIndexPageRenders(TestCase):
    def setUp(self) -> None:
        self.home_page = HomePageFactory.create()
        Site.objects.all().delete()
        Site.objects.create(
            hostname="testserver",
            root_page=self.home_page,
            is_default_site=True,
        )
        Site.clear_site_root_paths_cache()
        self.addCleanup(Site.clear_site_root_paths_cache)

    def test_product_index_page_renders(self) -> None:
        """Test that the product index page renders without a template error."""
        product_index_page = ProductIndexPageFactory.create()
        product_index_page.save_revision().publish()

        # BookFactory does not set an image, so this also exercises the
        # template's handling of a book with no image.
        book = BookFactory.create()
        book.save_revision().publish()

        response = self.client.get(product_index_page.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, book.title)


class TestProductGetContext(TestCase):
    def test_product_get_context(self) -> None:
        """Test that a Topic can be created."""
        product = ProductFactory.create()
        context = product.get_context(request=None)

        self.assertIn(
            "cart_add_product_form",
            context,
        )
        self.assertIsInstance(
            context["cart_add_product_form"],
            CartAddProductForm,
        )


class TestBookPageRenders(TestCase):
    def setUp(self) -> None:
        self.home_page = HomePageFactory.create()
        Site.objects.all().delete()
        Site.objects.create(
            hostname="testserver",
            root_page=self.home_page,
            is_default_site=True,
        )
        Site.clear_site_root_paths_cache()
        self.addCleanup(Site.clear_site_root_paths_cache)

    def test_book_cover_alt_text_includes_book_title(self) -> None:
        """Template variables inside {% image %} arguments are not interpolated,
        so the alt text must be built with a filter rather than {{ }}."""
        ProductIndexPageFactory.create().save_revision().publish()
        cover = Image.objects.create(title="cover", file=get_test_image_file())
        book = BookFactory.create(title="Faith and Practice", image=cover)
        book.save_revision().publish()

        response = self.client.get(book.url)

        self.assertContains(response, 'alt="Cover of Faith and Practice"')
        self.assertNotContains(response, "{{ page.title }}")

    def test_product_image_alt_text_includes_product_title(self) -> None:
        ProductIndexPageFactory.create().save_revision().publish()
        image = Image.objects.create(title="product", file=get_test_image_file())
        product = ProductFactory.create(title="Quaker Mug", image=image)
        product.save_revision().publish()

        response = self.client.get(product.url)

        self.assertContains(response, 'alt="Product image of Quaker Mug"')
