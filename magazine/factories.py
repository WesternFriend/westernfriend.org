from django.utils.text import slugify
from typing import Any
import factory
from home.factories import HomePageFactory

from home.models import HomePage
from .models import (
    MagazineArticle,
    MagazineDepartment,
    MagazineIssue,
    MagazineIndexPage,
)


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


class MagazineDepartmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MagazineDepartment

    title = factory.Faker("sentence", nb_words=4)  # type: ignore
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[MagazineDepartment],
        *args: Any,
        **kwargs: Any,
    ) -> MagazineDepartment:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = MagazineIndexPage.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            magazine_index_page = MagazineIndexPageFactory.create()
            magazine_index_page.add_child(instance=instance)
        return instance


class MagazineArticleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MagazineArticle

    title = factory.Faker("sentence", nb_words=4)  # type: ignore
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore
    department = factory.SubFactory(MagazineDepartmentFactory)  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[MagazineArticle],
        *args: Any,
        **kwargs: Any,
    ) -> MagazineArticle:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = MagazineIssue.objects.first()
        if parent:
            parent.add_child(instance=instance)
        else:
            magazine_issue = MagazineIssueFactory.create()
            magazine_issue.add_child(instance=instance)
        return instance
