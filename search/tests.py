from django.test import TestCase, Client
from django.urls import reverse
from wagtail.models import Page
from wagtail.search.models import Query
from unittest.mock import Mock, patch


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

    def test_search_no_query(self) -> None:
        response = self.client.get(reverse("search"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["paginated_search_results"].page), 0)

    def test_search_query(self) -> None:
        response = self.client.get(
            reverse("search"),
            {"query": "Test"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["paginated_search_results"].page), 3)

    def test_search_pagination_non_existant_page_default_first(self) -> None:
        response = self.client.get(
            reverse("search"),
            {
                "query": "Test",
                "page": 2,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["paginated_search_results"].page), 3)

    @patch.object(Query, "add_hit")
    def test_search_query_hit(self, mock_add_hit: Mock) -> None:
        self.client.get("/search/?query=Test")
        mock_add_hit.assert_called_once()

    def test_search_pagination_invalid_page(self) -> None:
        response = self.client.get("/search/?query=Test&page=abc")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["paginated_search_results"].page.number, 1)

    def test_search_pagination_out_of_range(self) -> None:
        response = self.client.get("/search/?query=Test&page=100")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["paginated_search_results"].page.number, 1)
