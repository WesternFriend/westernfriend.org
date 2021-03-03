import csv

from django.core.management.base import BaseCommand, CommandError

from tqdm import tqdm

from facets.models import (
    AudienceIndexPage,
    Audience,
    GenreIndexPage,
    Genre,
    MediumIndexPage,
    Medium,
    TimePeriodIndexPage,
    TimePeriod,
    TopicIndexPage,
    Topic,
)

facets = [
    {
        "file_name": "library_item_audience.csv",
        "index_page": AudienceIndexPage,
        "facet_class": Audience,
    },
    {
        "file_name": "library_item_genre.csv",
        "index_page": GenreIndexPage,
        "facet_class": Genre,
    },
    {
        "file_name": "library_item_medium.csv",
        "index_page": MediumIndexPage,
        "facet_class": Medium,
    },
    {
        "file_name": "library_item_time_period.csv",
        "index_page": TimePeriodIndexPage,
        "facet_class": TimePeriod,
    },
    {
        "file_name": "library_item_topic.csv",
        "index_page": TopicIndexPage,
        "facet_class": Topic,
    },
]

class Command(BaseCommand):
    help = "Import all library items"

    def add_arguments(self, parser):
        parser.add_argument("--folder", action="store", type=str)

    def handle(self, *args, **options):

        for facet in tqdm(
                facets, 
                desc="Library item facets",
                unit="taxonomy"
            ):
            # Get the only index page instance for this facet
            facet_index_page = facet["index_page"].objects.get()

            file_path = options["folder"] + facet["file_name"]

            with open(file_path) as import_file:
                facet_items = list(
                    csv.DictReader(import_file)
                )

                for facet_item in facet_items:
                    facet_instance = facet["facet_class"](
                        title=facet_item["drupal_full_name"]
                    )

                    facet_index_page.add_child(instance=facet_instance)
                    facet_index_page.save()
