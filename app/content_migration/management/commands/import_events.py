import csv
from datetime import datetime

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm
from wagtail.rich_text import RichText

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

        events_list = pd.read_csv(options["file"]).to_dict("records")

        for event in tqdm(events_list, desc="events", unit="row"):
            event_exists = Event.objects.filter(
                drupal_node_id=event["node_id"],
            ).exists()

            if not event_exists:
                # Convert event date strings into Python dates
                start_date = datetime.strptime(event["start_date"], date_format)
                end_date = datetime.strptime(event["end_date"], date_format)

                # # Get teaser, max length is 100 characters
                teaser = event["body"][0:99]

                event_body_blocks = []
                # Create rich text block for event body blocks list
                rich_text_block = ("rich_text", RichText(event["body"]))
                event_body_blocks.append(rich_text_block)

                import_event = Event(
                    title=event["title"],
                    body=event_body_blocks,
                    teaser=teaser,
                    start_date=start_date,
                    end_date=end_date,
                    website=event["event_link"],
                )

                # Add event to site page hiererchy
                events_index_page.add_child(instance=import_event)
                events_index_page.save()

        self.stdout.write("All done!")
