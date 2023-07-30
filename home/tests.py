from django.test import TestCase
from wagtail.models import Page

from home.models import HomePage
from .factories import HomePageFactory


class HomePageFactoryTest(TestCase):
    def test_home_page_creation(self) -> None:
        home_page = HomePageFactory.create()

        # Now test that it was created
        self.assertIsNotNone(home_page)
        self.assertIsInstance(
            home_page,
            HomePage,
        )

        # Verify the home page is a direct child of the root page
        self.assertEqual(
            home_page.get_parent(),
            Page.get_first_root_node(),
        )
