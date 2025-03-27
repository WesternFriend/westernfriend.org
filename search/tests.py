from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from wagtail.models import Page
from wagtail.search.backends import get_search_backend


class SearchViewTestCase(TestCase):
    def setUp(self) -> None:
        self.client = Client()

        # get the root page
        root_page = Page.objects.first()

        # add test pages as children of the root
        self.page1 = Page(title="Test Page 1")
        root_page.add_child(instance=self.page1)

        self.page2 = Page(title="Test Page 2")
        root_page.add_child(instance=self.page2)

        self.page3 = Page(title="Test Page 3")
        root_page.add_child(instance=self.page3)

        self.page1.save()
        self.page2.save()
        self.page3.save()

        # Update the search index to make the pages searchable
        search_backend = get_search_backend()
        # Add pages one by one to the search index
        for page in Page.objects.all():
            search_backend.add(page)

    def test_search_no_query(self) -> None:
        response = self.client.get(reverse("search"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context["paginated_search_results"].page), 0)

    def test_search_query(self) -> None:
        response = self.client.get(
            reverse("search"),
            {"query": "Test"},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context["paginated_search_results"].page), 3)

    def test_search_pagination_non_existant_page_default_first(self) -> None:
        response = self.client.get(
            reverse("search"),
            {
                "query": "Test",
                "page": 2,
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context["paginated_search_results"].page), 3)

    def test_search_pagination_invalid_page(self) -> None:
        response = self.client.get("/search/?query=Test&page=abc")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["paginated_search_results"].page.number, 1)

    def test_search_pagination_out_of_range(self) -> None:
        response = self.client.get("/search/?query=Test&page=100")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["paginated_search_results"].page.number, 1)
