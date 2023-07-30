from django.test import TestCase
from wagtail.models import Page
from .factories import HomePageFactory


class HomePageFactoryTest(TestCase):
    def test_home_page_creation(self) -> None:
        home_page = HomePageFactory.create()
        self.assertIsInstance(home_page, Page)
        self.assertIsNotNone(
            home_page.pk,
        )  # pk should be set, indicating the page was saved

        # Verify the home page is a direct child of the root page
        self.assertEqual(home_page.get_parent(), Page.get_first_root_node())
