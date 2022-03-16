import csv
from datetime import datetime

from tqdm import tqdm

from django.core.management.base import BaseCommand, CommandError

from events.models import Event, EventsIndexPage

# Event dates are in ISO 8601 format
date_format = "%Y-%m-%dT%H:%M:%S%z"


class Command(BaseCommand):
    help = "Import Departments from Drupal site"

    def add_arguments(self, parser):
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args, **options):
        # Get the only instance of Magazine Department Index Page
        events_index_page = EventsIndexPage.objects.get()

        with open(options["file"]) as import_file:
            events = csv.DictReader(import_file)
            events_list = list(events)

            for event in tqdm(events_list, desc="events", unit="row"):
                event_exists = Event.objects.filter(
                    drupal_node_id=event["node_id"],
                ).exists()

                # Convert event date strings into Python dates
                start_date = datetime.strptime(event["start_date"], date_format)
                end_date = datetime.strptime(event["end_date"], date_format)

                # Get teaser, max length is 100 characters
                teaser = event["body"][0:99]

                if not event_exists:
                    import_event = Event(
                        title=event["title"],
                        body=event["body"],
                        teaser=teaser,
                        start_date=start_date,
                        end_date=end_date,
                        website=event["event_link"],
                    )

                    # Add event to site page hiererchy
                    events_index_page.add_child(instance=import_event)
                    events_index_page.save()

        self.stdout.write("All done!")
