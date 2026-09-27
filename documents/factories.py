from typing import Any

import factory
from factory.django import DjangoModelFactory

from common.fake_content import stream_body
from contact.factories import MeetingFactory
from home.factories import HomePageFactory
from home.models import HomePage

from .models import (
    MeetingDocument,
    MeetingDocumentIndexPage,
    PublicBoardDocument,
    PublicBoardDocumentIndexPage,
)


class MeetingDocumentIndexPageFactory(DjangoModelFactory):
    class Meta:
        model = MeetingDocumentIndexPage

    title = factory.Sequence(lambda n: f"Meeting Documents {n}")  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[MeetingDocumentIndexPage],
        *args: Any,
        **kwargs: Any,
    ) -> MeetingDocumentIndexPage:
        instance = model_class(*args, **kwargs)  # type: ignore
        home_page = HomePage.objects.first() or HomePageFactory.create()
        home_page.add_child(instance=instance)
        return instance


class MeetingDocumentFactory(DjangoModelFactory):
    class Meta:
        model = MeetingDocument

    class Params:
        # Pools the seeder passes in so bodies can show images and link
        # to other pages; tests leave them empty.
        body_images = None
        body_links = None

    publication_date = factory.Faker("date_between", start_date="-5y")  # type: ignore
    publishing_meeting = factory.SubFactory(MeetingFactory)  # type: ignore
    document_type = factory.Faker(  # type: ignore
        "random_element",
        elements=MeetingDocument.MeetingDocmentTypeChoices.values,
    )

    @factory.lazy_attribute  # type: ignore
    def title(self) -> str:
        label = MeetingDocument.MeetingDocmentTypeChoices(self.document_type).label
        return f"{self.publishing_meeting.title} {label}, {self.publication_date:%Y}"

    body = factory.LazyAttribute(  # type: ignore
        lambda obj: stream_body(
            images=obj.body_images,
            link_pages=obj.body_links,
            sections=2,
        ),
    )

    @classmethod
    def _create(
        cls,
        model_class: type[MeetingDocument],
        *args: Any,
        **kwargs: Any,
    ) -> MeetingDocument:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = (
            MeetingDocumentIndexPage.objects.first()
            or MeetingDocumentIndexPageFactory.create()
        )
        parent.add_child(instance=instance)
        return instance


class PublicBoardDocumentIndexPageFactory(DjangoModelFactory):
    class Meta:
        model = PublicBoardDocumentIndexPage

    title = factory.Sequence(lambda n: f"Board Documents {n}")  # type: ignore

    @classmethod
    def _create(
        cls,
        model_class: type[PublicBoardDocumentIndexPage],
        *args: Any,
        **kwargs: Any,
    ) -> PublicBoardDocumentIndexPage:
        instance = model_class(*args, **kwargs)  # type: ignore
        home_page = HomePage.objects.first() or HomePageFactory.create()
        home_page.add_child(instance=instance)
        return instance


class PublicBoardDocumentFactory(DjangoModelFactory):
    class Meta:
        model = PublicBoardDocument

    class Params:
        # Pools the seeder passes in so bodies can show images and link
        # to other pages; tests leave them empty.
        body_images = None
        body_links = None

    title = factory.Faker("sentence", nb_words=5)  # type: ignore
    publication_date = factory.Faker("date_between", start_date="-5y")  # type: ignore
    category = factory.Faker(  # type: ignore
        "random_element",
        elements=PublicBoardDocument.PublicBoardDocmentCategoryChoices.values,
    )
    body = factory.LazyAttribute(  # type: ignore
        lambda obj: stream_body(
            images=obj.body_images,
            link_pages=obj.body_links,
            sections=2,
        ),
    )

    @classmethod
    def _create(
        cls,
        model_class: type[PublicBoardDocument],
        *args: Any,
        **kwargs: Any,
    ) -> PublicBoardDocument:
        instance = model_class(*args, **kwargs)  # type: ignore
        parent = (
            PublicBoardDocumentIndexPage.objects.first()
            or PublicBoardDocumentIndexPageFactory.create()
        )
        parent.add_child(instance=instance)
        return instance
