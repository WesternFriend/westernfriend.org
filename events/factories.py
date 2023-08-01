import factory
from factory.django import DjangoModelFactory
from django.utils.text import slugify
import pytz
from wagtail.models import Page

from events.models import EventsIndexPage, Event
from home.factories import HomePageFactory
from home.models import HomePage


class EventsIndexPageFactory(DjangoModelFactory):
    class Meta:
        model = EventsIndexPage

    # You can add additional field definitions here if you need them
    title = factory.Faker("sentence", nb_words=4)  # type: ignore
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore
    intro = factory.Faker("text")  # type: ignore
    depth = factory.Sequence(lambda n: n + 3)  # Assumes that HomePage page depth is 1

    @factory.lazy_attribute  # type: ignore
    def path(self):
        # Constructs a valid path by appending self.depth
        # to the path of root page
        root_path = Page.get_first_root_node().path
        return f"{root_path}{str(self.depth).zfill(4)}"

    @classmethod
    def _create(cls, model_class, *args, **kwargs) -> EventsIndexPage:  # type: ignore
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

    title = factory.Faker("sentence", nb_words=4)  # type: ignore
    start_date = factory.Faker("date_time", tzinfo=pytz.UTC)  # type: ignore

    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))  # type: ignore
    depth = factory.Sequence(lambda n: n + 4)  # Assumes that HomePage page depth is 1

    @factory.lazy_attribute  # type: ignore
    def path(self):
        # Constructs a valid path by appending self.depth
        # to the path of root page
        root_path = Page.get_first_root_node().path
        return f"{root_path}{str(self.depth).zfill(4)}"

    @classmethod
    def _create(cls, model_class, *args, **kwargs) -> Event:  # type: ignore
        instance = model_class(*args, **kwargs)
        parent = EventsIndexPage.objects.first()

        if parent:
            parent.add_child(instance=instance)
        else:
            event_index_page = EventsIndexPageFactory.create()
            event_index_page.add_child(instance=instance)
        return instance
