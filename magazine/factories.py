from django.utils.text import slugify
from typing import Any
import factory
from home.factories import HomePageFactory

from home.models import HomePage
from .models import MagazineIssue, MagazineIndexPage


class MagazineIndexPageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MagazineIndexPage

    title = factory.Faker("sentence", nb_words=4)  # type: ignore
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[MagazineIndexPage],
        *args: Any,
        **kwargs: Any,
    ) -> MagazineIndexPage:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = HomePage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            home_page = HomePageFactory.create()
            home_page.add_child(instance=instance)

        return instance


class MagazineIssueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MagazineIssue

    title = factory.Sequence(lambda n: f"Issue {n}")
    publication_date = factory.Faker("date_time_this_year", before_now=False)  # type: ignore # noqa: E501
    issue_number = factory.Faker("pyint", min_value=1, max_value=100)  # type: ignore
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[MagazineIssue],
        *args: Any,
        **kwargs: Any,
    ) -> MagazineIssue:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = MagazineIndexPage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            home_page = MagazineIndexPageFactory.create()
            home_page.add_child(instance=instance)
        return instance
