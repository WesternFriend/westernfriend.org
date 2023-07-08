from tqdm import tqdm
from content_migration.management.shared import parse_csv_file

from facets.models import (
    Audience,
    AudienceIndexPage,
    Genre,
    GenreIndexPage,
    Medium,
    MediumIndexPage,
    TimePeriod,
    TimePeriodIndexPage,
    Topic,
    TopicIndexPage,
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


def handle_import_library_item_facets(folder: str) -> None:
    for facet in tqdm(facets, desc="Library item facets", unit="taxonomy"):
        # Get the only index page instance for this facet
        facet_index_page = facet["index_page"].objects.get()  # type: ignore

        file_path = folder + facet["file_name"]  # type: ignore

        facet_items = parse_csv_file(file_path)

        for facet_item in facet_items:
            if (
                not facet["facet_class"]  # type: ignore
                .objects.filter(title=facet_item["drupal_full_name"])
                .exists()
            ):
                facet_instance = facet["facet_class"](  # type: ignore
                    title=facet_item["drupal_full_name"],
                )

                facet_index_page.add_child(instance=facet_instance)
                facet_index_page.save()
