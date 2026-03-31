from django.test import RequestFactory, TestCase
from wagtail.models import Page, Site

from home.models import HomePage
from wf_pages.models import MollyWingateBlogIndexPage, MollyWingateBlogPage


class TestMollyWingateBlogIndexPage(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()

        # Set up the page hierarchy
        site_root = Page.objects.get(id=2)
        self.home_page = HomePage(title="Home")
        site_root.add_child(instance=self.home_page)
        Site.objects.all().update(root_page=self.home_page)

        self.blog_index = MollyWingateBlogIndexPage(title="Molly Wingate Blog")
        self.home_page.add_child(instance=self.blog_index)

    def test_get_context(self) -> None:
        """Test that get_context returns blog posts ordered by publication date."""
        import datetime

        # Create blog posts with different dates
        blog_post_1 = MollyWingateBlogPage(
            title="First Post",
            publication_date=datetime.date.today() - datetime.timedelta(days=2),
        )
        blog_post_2 = MollyWingateBlogPage(
            title="Second Post",
            publication_date=datetime.date.today() - datetime.timedelta(days=1),
        )
        blog_post_3 = MollyWingateBlogPage(
            title="Third Post",
            publication_date=datetime.date.today(),
        )

        self.blog_index.add_child(instance=blog_post_1)
        self.blog_index.add_child(instance=blog_post_2)
        self.blog_index.add_child(instance=blog_post_3)

        request = self.factory.get("/")
        context = self.blog_index.get_context(request)

        self.assertIn("blog_posts", context)
        blog_posts = list(context["blog_posts"])
        self.assertEqual(len(blog_posts), 3)
        # Check that posts are ordered by publication date (newest first)
        self.assertEqual(blog_posts[0].title, "Third Post")
        self.assertEqual(blog_posts[1].title, "Second Post")
        self.assertEqual(blog_posts[2].title, "First Post")
