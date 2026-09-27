from typing import Any

import factory
from django.utils import timezone
from django.utils.text import slugify

from common.fake_content import ISSUE_THEMES, fake, headline, stream_body
from home.factories import HomePageFactory
from home.models import HomePage

from .models import (
    ArchiveArticle,
    ArchiveArticleAuthor,
    ArchiveIssue,
    DeepArchiveIndexPage,
    MagazineArticle,
    MagazineArticleAuthor,
    MagazineDepartment,
    MagazineIndexPage,
    MagazineIssue,
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

    publication_date = factory.LazyFunction(
        lambda: timezone.now() + timezone.timedelta(days=30),
    )
    # Consecutive bimonthly issues get different themes.
    title = factory.LazyAttribute(  # type: ignore
        lambda obj: ISSUE_THEMES[
            (obj.publication_date.year * 12 + obj.publication_date.month)
            // 2
            % len(ISSUE_THEMES)
        ],
    )
    slug = factory.Sequence(lambda n: f"issue-{n}")  # type: ignore
    issue_number = factory.Faker("pyint", min_value=1, max_value=100)  # type: ignore

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

    class Params:
        # Pools the seeder passes in so bodies can show images and link
        # to other pages; tests leave them empty.
        body_images = None
        body_links = None

    title = factory.LazyFunction(headline)  # type: ignore
    slug = factory.Sequence(lambda n: f"article-{n}")  # type: ignore
    teaser = factory.LazyFunction(  # type: ignore
        lambda: f"<p>{fake.sentence(nb_words=20)}</p>",
    )
    body = factory.LazyAttribute(  # type: ignore
        lambda obj: stream_body(
            images=obj.body_images,
            link_pages=obj.body_links,
            sections=fake.random_int(2, 4),
        ),
    )
    department = factory.SubFactory(MagazineDepartmentFactory)  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[MagazineArticle],
        *args: Any,
        **kwargs: Any,
    ) -> MagazineArticle:
        # Extract parent argument if provided
        parent = kwargs.pop("parent", None)

        instance = model_class(*args, **kwargs)  # type: ignore

        # Use provided parent or find/create a default one
        if parent:
            parent.add_child(instance=instance)
        else:
            default_parent = MagazineIssue.objects.order_by("id").first()
            if default_parent:
                default_parent.add_child(instance=instance)
            else:
                magazine_issue = MagazineIssueFactory.create()
                magazine_issue.add_child(instance=instance)
        return instance


class DeepArchiveIndexPageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DeepArchiveIndexPage

    title = factory.Sequence(lambda n: f"Deep Archive {n}")

    @classmethod
    def _create(
        cls,
        model_class: type[DeepArchiveIndexPage],
        *args: Any,
        **kwargs: Any,
    ) -> DeepArchiveIndexPage:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = MagazineIndexPage.objects.first() or MagazineIndexPageFactory.create()
        parent.add_child(instance=instance)
        return instance


def _add_table_of_contents(
    issue: ArchiveIssue,
    *,
    create: bool,
    count: int | None,
) -> None:
    """Add ``count`` articles (default 2 to 6) to an archive issue's contents."""
    if count is None:
        count = fake.random_int(2, 6)
    issue.archive_articles = [
        ArchiveArticleFactory.build(toc_page_number=3 * position + 1)
        for position in range(count)
    ]
    if create:
        issue.save()


class ArchiveIssueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ArchiveIssue

    publication_date = factory.Faker("date_between", start_date="-90y", end_date="-20y")  # type: ignore
    title = factory.LazyAttribute(  # type: ignore
        lambda obj: f"Friends Bulletin, {obj.publication_date:%B %Y}",
    )
    internet_archive_identifier = factory.Sequence(  # type: ignore
        lambda n: f"westernfriend-archive-{n:04d}",
    )
    western_friend_volume = factory.Sequence(lambda n: f"Volume {n}")  # type: ignore
    # Tables of contents are plain data, so the factory fills them in.
    archive_articles = factory.PostGeneration(  # type: ignore
        lambda issue, create, extracted, **_kwargs: _add_table_of_contents(
            issue,
            create=create,
            count=extracted,
        ),
    )

    @classmethod
    def _create(
        cls,
        model_class: type[ArchiveIssue],
        *args: Any,
        **kwargs: Any,
    ) -> ArchiveIssue:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = (
            DeepArchiveIndexPage.objects.first() or DeepArchiveIndexPageFactory.create()
        )
        parent.add_child(instance=instance)
        return instance


class MagazineArticleAuthorFactory(factory.django.DjangoModelFactory):
    """Author link; pass ``author=`` and attach via the article's cluster."""

    class Meta:
        model = MagazineArticleAuthor


class ArchiveArticleAuthorFactory(factory.django.DjangoModelFactory):
    """Author link; pass ``author=`` and attach via the archive article's cluster."""

    class Meta:
        model = ArchiveArticleAuthor


class ArchiveArticleFactory(factory.django.DjangoModelFactory):
    """Table-of-contents entry for an ArchiveIssue.

    Pass ``issue=`` with a saved issue, or attach built instances to the
    issue's ``archive_articles`` cluster before saving it.
    """

    class Meta:
        model = ArchiveArticle

    title = factory.LazyFunction(headline)  # type: ignore
    toc_page_number = factory.Sequence(lambda n: n + 1)  # type: ignore
    pdf_page_number = factory.LazyAttribute(lambda obj: obj.toc_page_number + 2)  # type: ignore
