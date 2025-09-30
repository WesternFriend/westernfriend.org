from django.core.management.base import BaseCommand

from facets.factories import (
    AudienceFactory,
    GenreFactory,
    MediumFactory,
    TimePeriodFactory,
    TopicFactory,
)

from facets.models import (
    AudienceIndexPage,
    GenreIndexPage,
    MediumIndexPage,
    TimePeriodIndexPage,
    TopicIndexPage,
)


class Command(BaseCommand):
    help = "Generate random facets"

    def handle(self, *args: tuple, **options: dict) -> None:
        self.stdout.write("Creating random facets...")
        audience_index_page = AudienceIndexPage.objects.first()
        genre_index_page = GenreIndexPage.objects.first()
        medium_index_page = MediumIndexPage.objects.first()
        time_period_index_page = TimePeriodIndexPage.objects.first()
        topic_index_page = TopicIndexPage.objects.first()

        number_of_audiences = 10
        number_of_genres = 10
        number_of_media = 10
        number_of_time_periods = 10
        number_of_topics = 10

        for _ in range(number_of_audiences):
            audience = AudienceFactory.build()
            audience_index_page.add_child(instance=audience)

        for _ in range(number_of_genres):
            genre = GenreFactory.build()
            genre_index_page.add_child(instance=genre)

        for _ in range(number_of_media):
            medium = MediumFactory.build()
            medium_index_page.add_child(instance=medium)

        for _ in range(number_of_time_periods):
            time_period = TimePeriodFactory.build()
            time_period_index_page.add_child(instance=time_period)

        for _ in range(number_of_topics):
            topic = TopicFactory.build()
            topic_index_page.add_child(instance=topic)

        self.stdout.write(self.style.SUCCESS("Successfully created facets"))
