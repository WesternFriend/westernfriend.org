from django.test import TestCase
from contact.factories import PersonFactory
from .models import Memorial


class MemorialModelTest(TestCase):
    def setUp(self) -> None:
        self.person = PersonFactory(
            given_name="John",
            family_name="Woolman",
        )

    def test_full_name(self) -> None:
        memorial = Memorial(  # type: ignore
            memorial_person=self.person,
        )
        self.assertEqual(
            memorial.full_name(),
            "John Woolman",
        )
