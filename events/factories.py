import datetime
from typing import Any

import factory
from django.utils.text import slugify
from factory.django import DjangoModelFactory
from wagtail.models import Page

from common.fake_content import (
    EVENT_KINDS,
    WESTERN_TIMEZONES,
    fake,
    headline,
    stream_body,
)
from events.models import Event, EventsIndexPage
from home.factories import HomePageFactory
from home.models import HomePage


class EventsIndexPageFactory(DjangoModelFactory):
    class Meta:
        model = EventsIndexPage

    # You can add additional field definitions here if you need them
    title = factory.Faker("sentence", nb_words=4)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))
    intro = factory.Faker("text")
    depth = factory.Sequence(lambda n: n + 3)  # Assumes that HomePage page depth is 1

    @factory.lazy_attribute
    def path(self):
        # Constructs a valid path by appending self.depth
        # to the path of root page
        root_path = Page.get_first_root_node().path
        return f"{root_path}{str(self.depth).zfill(4)}"

    @classmethod
    def _create(cls, model_class, *args, **kwargs) -> EventsIndexPage:
        instance = model_class(*args, **kwargs)
        parent = HomePage.objects.first()

        if parent:
            parent.add_child(instance=instance)
        else:
            home_page = HomePageFactory.create()
            home_page.add_child(instance=instance)
        return instance


def _event_body(obj: Any) -> list[dict]:
    return stream_body(images=obj.body_images, link_pages=obj.body_links, sections=1)


class EventFactory(DjangoModelFactory):
    class Meta:
        model = Event

    class Params:
        body_images = None
        body_links = None
        # An event that has already ended, so it drops off the listings.
        past = factory.Trait(
            start_date=factory.Faker(
                "date_time_between",
                start_date="-365d",
                end_date="-5d",
                tzinfo=datetime.UTC,
            ),
            end_date=None,
        )
        # "Other" events are listed separately from Western Friend's own.
        other_category = factory.Trait(category=Event.EventCategoryChoices.OTHER)

    title = factory.LazyFunction(  # type: ignore
        lambda: f"{fake.random_element(EVENT_KINDS)}: {headline()}",
    )
    teaser = factory.LazyFunction(lambda: fake.sentence(nb_words=10)[:100])  # type: ignore
    body = factory.LazyAttribute(_event_body)  # type: ignore
    start_date = factory.Faker(
        "future_datetime",
        end_date="+90d",
        tzinfo=datetime.UTC,
    )
    # Most events have an end: an afternoon, an evening, or a weekend.
    end_date = factory.LazyAttribute(  # type: ignore
        lambda obj: (
            obj.start_date
            + datetime.timedelta(hours=fake.random_element([2, 3, 26, 50]))
            if fake.boolean(chance_of_getting_true=70)
            else None
        ),
    )
    timezone = factory.Faker("random_element", elements=WESTERN_TIMEZONES)  # type: ignore
    website = factory.Maybe(  # type: ignore
        factory.Faker("boolean"),
        yes_declaration=factory.Faker("url"),
        no_declaration="",
    )

    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))
    depth = factory.Sequence(lambda n: n + 4)  # Assumes that HomePage page depth is 1

    @factory.lazy_attribute
    def path(self):
        # Constructs a valid path by appending self.depth
        # to the path of root page
        root_path = Page.get_first_root_node().path
        return f"{root_path}{str(self.depth).zfill(4)}"

    @classmethod
    def _create(cls, model_class, *args, **kwargs) -> Event:
        instance = model_class(*args, **kwargs)
        parent = EventsIndexPage.objects.first()

        if parent:
            parent.add_child(instance=instance)
        else:
            event_index_page = EventsIndexPageFactory.create()
            event_index_page.add_child(instance=instance)
        return instance
