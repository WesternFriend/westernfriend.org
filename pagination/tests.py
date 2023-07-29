from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.test import TestCase
from django_stubs_ext import QuerySetAny

from accounts.factories import UserFactory

from .helpers import get_paginated_items, PaginatorPageWithElidedPageRange

User = get_user_model()


class GetPaginatedItemsTests(TestCase):
    users: QuerySetAny

    @classmethod
    def setUpTestData(cls) -> None:
        UserFactory.create_batch(200)
        cls.users = User.objects.all()

    def test_page_number_is_none(self) -> None:
        result: PaginatorPageWithElidedPageRange = get_paginated_items(
            self.users,
            items_per_page=9,
        )
        expected_result_number = 1
        self.assertEqual(
            result.page.number,
            expected_result_number,
        )

    def test_page_number_is_digit(self) -> None:
        result: PaginatorPageWithElidedPageRange = get_paginated_items(
            self.users,
            items_per_page=9,
            page_number="3",
        )
        expected_result_number = 3
        self.assertEqual(
            result.page.number,
            expected_result_number,
        )

    def test_page_number_is_not_digit(self) -> None:
        result: PaginatorPageWithElidedPageRange = get_paginated_items(
            self.users,
            items_per_page=9,
            page_number="abc",
        )
        expected_result_number = 1
        self.assertEqual(
            result.page.number,
            expected_result_number,
        )

    def test_page_number_greater_than_total_pages(self) -> None:
        result: PaginatorPageWithElidedPageRange = get_paginated_items(
            self.users,
            items_per_page=9,
            page_number="100",
        )
        expected_result_number = 1
        self.assertEqual(
            result.page.number,
            expected_result_number,
        )

    def test_items_per_page(self) -> None:
        result: PaginatorPageWithElidedPageRange = get_paginated_items(
            self.users,
            items_per_page=9,
            page_number="1",
        )
        expected_len_result = 9
        self.assertEqual(
            len(result.page),
            expected_len_result,
        )

    def test_elided_page_range(self) -> None:
        result: PaginatorPageWithElidedPageRange = get_paginated_items(
            self.users,
            items_per_page=9,
            page_number="10",
        )
        self.assertEqual(
            list(result.elided_page_range),
            [
                1,
                2,
                Paginator.ELLIPSIS,  # type: ignore
                7,
                8,
                9,
                10,
                11,
                12,
                13,
                Paginator.ELLIPSIS,  # type: ignore
                22,
                23,
            ],
        )

    def test_elided_page_range_first_page(self) -> None:
        result: PaginatorPageWithElidedPageRange = get_paginated_items(
            self.users,
            items_per_page=9,
            page_number="1",
        )
        self.assertEqual(
            list(result.elided_page_range),
            [
                1,
                2,
                3,
                4,
                Paginator.ELLIPSIS,  # type: ignore
                22,
                23,
            ],
        )

    def test_elided_page_range_last_page(self) -> None:
        result: PaginatorPageWithElidedPageRange = get_paginated_items(
            self.users,
            items_per_page=9,
            page_number="23",
        )
        self.assertEqual(
            list(result.elided_page_range),
            [
                1,
                2,
                Paginator.ELLIPSIS,  # type: ignore
                20,
                21,
                22,
                23,
            ],
        )
