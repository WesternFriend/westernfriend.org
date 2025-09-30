import datetime

import factory
from django.utils.text import slugify
from factory.django import DjangoModelFactory
from wagtail.models import Page

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


class EventFactory(DjangoModelFactory):
    class Meta:
        model = Event

    title = factory.Faker("sentence", nb_words=5)
    start_date = factory.Faker(
        "future_datetime",
        end_date="+90d",
        tzinfo=datetime.UTC,
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
