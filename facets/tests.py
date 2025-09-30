from django.test import RequestFactory, TestCase

from facets.models import Audience, FacetIndexPage, Genre, Medium, TimePeriod, Topic
from library.factories import LibraryItemFactory
from library.models import LibraryIndexPage, LibraryItemTopic
from .factories import (
    FacetIndexPageFactory,
    AudienceFactory,
    GenreFactory,
    MediumFactory,
    TimePeriodFactory,
    TopicFactory,
)


class TestFacetIndexPage(TestCase):
    def test_facet_index_page_creation(self) -> None:
        """Test that a FacetIndexPage can be created."""
        facet_index_page = FacetIndexPageFactory.create()

        self.assertIsInstance(
            facet_index_page,
            FacetIndexPage,
        )

        self.assertIsInstance(
            facet_index_page.get_parent().specific,
            LibraryIndexPage,
        )


class TestAudience(TestCase):
    def test_audience_creation(self) -> None:
        """Test that an Audience can be created."""
        audience = AudienceFactory.create()

        self.assertIsInstance(
            audience,
            Audience,
        )

        self.assertIsInstance(
            audience.get_parent().specific,
            FacetIndexPage,
        )


class TestGenre(TestCase):
    def test_genre_creation(self) -> None:
        """Test that a Genre can be created."""
        genre = GenreFactory.create()

        self.assertIsInstance(
            genre,
            Genre,
        )

        self.assertIsInstance(
            genre.get_parent().specific,
            FacetIndexPage,
        )


class TestMedium(TestCase):
    def test_medium_creation(self) -> None:
        """Test that a Medium can be created."""
        medium = MediumFactory.create()

        self.assertIsInstance(
            medium,
            Medium,
        )

        self.assertIsInstance(
            medium.get_parent().specific,
            FacetIndexPage,
        )


class TestTimePeriod(TestCase):
    def test_time_period_creation(self) -> None:
        """Test that a TimePeriod can be created."""
        time_period = TimePeriodFactory.create()

        self.assertIsInstance(
            time_period,
            TimePeriod,
        )

        self.assertIsInstance(
            time_period.get_parent().specific,
            FacetIndexPage,
        )


class TestTopic(TestCase):
    def test_topic_creation(self) -> None:
        """Test that a Topic can be created."""
        topic = TopicFactory.create()

        self.assertIsInstance(
            topic,
            Topic,
        )

        self.assertIsInstance(
            topic.get_parent().specific,
            FacetIndexPage,
        )


class TestTopicGetContext(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.topic = TopicFactory.create()

    def test_get_context(self) -> None:
        # Create some LibraryItem objects associated with the topic
        library_items = LibraryItemFactory.create_batch(5)

        for library_item in library_items:
            LibraryItemTopic.objects.create(
                topic=self.topic,
                library_item=library_item,
            )

        # Make a GET request
        request = self.factory.get("/")
        context = self.topic.get_context(request)

        # Check the context
        self.assertIn("library_items", context)

        # Get the primary keys of the LibraryItem instances in the context
        context_library_item_pks = [item.pk for item in context["library_items"]]

        # Check that the library_items in the context are correct
        self.assertListEqual(
            context_library_item_pks,
            list(
                self.topic.related_library_items.values_list(
                    "library_item",
                    flat=True,
                ),
            ),
        )
