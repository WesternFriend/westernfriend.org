from django.contrib.auth import get_user_model
from django.test import TestCase
from django_stubs_ext import QuerySetAny

from accounts.factories import UserFactory

from .helpers import get_paginated_items

User = get_user_model()


class GetPaginatedItemsTests(TestCase):
    users: QuerySetAny

    @classmethod
    def setUpTestData(cls) -> None:
        UserFactory.create_batch(20)
        cls.users = User.objects.all()

    def test_page_number_is_none(self) -> None:
        result = get_paginated_items(self.users, 9)
        self.assertEqual(result.number, 1)

    def test_page_number_is_digit(self) -> None:
        result = get_paginated_items(self.users, 9, "3")
        self.assertEqual(result.number, 3)

    def test_page_number_is_not_digit(self) -> None:
        result = get_paginated_items(self.users, 9, "abc")
        self.assertEqual(result.number, 1)

    def test_page_number_greater_than_total_pages(self) -> None:
        result = get_paginated_items(self.users, 9, "100")
        self.assertEqual(result.number, 1)

    def test_items_per_page(self) -> None:
        result = get_paginated_items(self.users, 9, "1")
        self.assertEqual(len(result), 9)
