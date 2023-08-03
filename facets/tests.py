from django.test import TestCase

from facets.models import Audience, FacetIndexPage, Genre, Medium, TimePeriod, Topic
from library.models import LibraryIndexPage
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
        self.assertIsNotNone(facet_index_page)
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
        self.assertIsNotNone(audience)
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
        self.assertIsNotNone(genre)
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
        self.assertIsNotNone(medium)
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
        self.assertIsNotNone(time_period)
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
        self.assertIsNotNone(topic)
        self.assertIsInstance(
            topic,
            Topic,
        )

        self.assertIsInstance(
            topic.get_parent().specific,
            FacetIndexPage,
        )
