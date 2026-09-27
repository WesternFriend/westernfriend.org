import datetime

from django.test import RequestFactory, TestCase
from django.utils import timezone
from wagtail.models import Page, Site

from home.models import HomePage
from wf_pages.factories import (
    MollyWingateBlogPageFactory,
    WfPageCollectionFactory,
    WfPageFactory,
)
from wf_pages.models import (
    MollyWingateBlogIndexPage,
    MollyWingateBlogPage,
    WfPageCollectionIndexPage,
)


class TestMollyWingateBlogIndexPage(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()

        # Set up the page hierarchy
        site_root = Page.get_first_root_node()
        self.home_page = HomePage(title="Home")
        site_root.add_child(instance=self.home_page)
        Site.objects.all().update(root_page=self.home_page)

        self.blog_index = MollyWingateBlogIndexPage(title="Molly Wingate Blog")
        self.home_page.add_child(instance=self.blog_index)

    def test_get_context(self) -> None:
        """Test that get_context returns blog posts ordered by publication date."""
        # Create blog posts with different dates and a duplicate date
        blog_post_1 = MollyWingateBlogPage(
            title="First Post",
            publication_date=timezone.localdate() - datetime.timedelta(days=2),
        )
        blog_post_2 = MollyWingateBlogPage(
            title="Second Post",
            publication_date=timezone.localdate() - datetime.timedelta(days=1),
        )
        blog_post_3 = MollyWingateBlogPage(
            title="Third Post",
            publication_date=timezone.localdate(),
        )
        blog_post_4 = MollyWingateBlogPage(
            title="Fourth Post",
            publication_date=timezone.localdate(),
        )

        self.blog_index.add_child(instance=blog_post_1)
        self.blog_index.add_child(instance=blog_post_2)
        self.blog_index.add_child(instance=blog_post_3)
        self.blog_index.add_child(instance=blog_post_4)

        request = self.factory.get("/")
        context = self.blog_index.get_context(request)

        self.assertIn("blog_posts", context)
        blog_posts = list(context["blog_posts"])
        self.assertEqual(len(blog_posts), 4)
        # Check that posts are ordered by publication date with a stable tie-breaker.
        self.assertEqual(blog_posts[0].title, "Fourth Post")
        self.assertEqual(blog_posts[1].title, "Third Post")
        self.assertEqual(blog_posts[2].title, "Second Post")
        self.assertEqual(blog_posts[3].title, "First Post")


class WfPageFactoryTest(TestCase):
    """The factories create a home page when there isn't one yet."""

    def test_wf_page_factory(self) -> None:
        page = WfPageFactory.create()

        self.assertIsInstance(page.get_parent().specific, HomePage)
        self.assertTrue(page.body)

    def test_blog_page_factory(self) -> None:
        post = MollyWingateBlogPageFactory.create()

        index_page = post.get_parent().specific
        self.assertIsInstance(index_page, MollyWingateBlogIndexPage)
        self.assertIsInstance(index_page.get_parent().specific, HomePage)
        self.assertIsNotNone(post.publication_date)

        second = MollyWingateBlogPageFactory.create()
        self.assertEqual(second.get_parent(), post.get_parent())

    def test_collection_factory(self) -> None:
        collection = WfPageCollectionFactory.create()

        self.assertIsInstance(
            collection.get_parent().specific,
            WfPageCollectionIndexPage,
        )
        second = WfPageCollectionFactory.create()
        self.assertEqual(second.get_parent(), collection.get_parent())
