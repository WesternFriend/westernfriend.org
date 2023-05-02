import logging
from datetime import datetime

import numpy as np
import pandas as pd
from django.core.management.base import BaseCommand
from tqdm import tqdm
from content_migration.management.commands.shared import (
    get_existing_magazine_author_from_db,
)


from memorials.models import Memorial, MemorialIndexPage

logging.basicConfig(
    filename="import_log_memorials.log",
    level=logging.ERROR,
    format="%(message)s",
    # format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import all memorial minutes"

    def add_arguments(self, parser):
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args, **options):
        # Get the only instance of Magazine Department Index Page
        memorial_index_page = MemorialIndexPage.objects.get()

        memorials = (
            pd.read_csv(options["file"]).replace({np.nan: None}).to_dict("records")
        )

        for memorial_data in tqdm(memorials, desc="Memorials", unit="row"):
            memorial_exists = Memorial.objects.filter(
                drupal_memorial_id=int(memorial_data["memorial_id"])
            ).exists()

            if memorial_exists:
                memorial = Memorial.objects.get(
                    drupal_memorial_id=int(memorial_data["memorial_id"])
                )
            else:
                memorial = Memorial(
                    drupal_memorial_id=int(memorial_data["memorial_id"]),
                )

            full_name = f'{memorial_data["First Name"]} {memorial_data["Last Name"]}'

            # Make sure we can find the related Meeting contact
            # otherwise, we can't link the memorial ot a meeting
            meeting_author_id = memorial_data["memorial_meeting_drupal_author_id"]

            if meeting_author_id is not None:
                memorial.memorial_meeting = get_existing_magazine_author_from_db(
                    meeting_author_id
                )
            else:
                logger.error(f"Meeting ID is null for {full_name}")
                # go to next item since all memorials should be linked to a meeting
                continue

            # Make sure we can find the related memorial person contact
            # otherwise, we can't link the memorial to a contact
            memorial_person_id = memorial_data["drupal_author_id"]
            memorial_person = get_existing_magazine_author_from_db(memorial_person_id)

            if memorial_person is not None:
                memorial.memorial_person = memorial_person
            else:
                message = (
                    f"Could not find memorial person contact: {memorial_person_id}"
                )
                logger.error(message)
                # go to next item since all memorials should be linked to an author contact
                continue

            memorial.title = full_name

            memorial.memorial_minute = memorial_data["body"]

            # Strip out time from datetime strings
            datetime_format = "%Y-%m-%dT%X"

            # Dates are optional
            if memorial_data["Date of Birth"] is not None:
                memorial.date_of_birth = datetime.strptime(
                    memorial_data["Date of Birth"], datetime_format
                )

            if memorial_data["Date of Death"] is not None:
                memorial.date_of_death = datetime.strptime(
                    memorial_data["Date of Death"], datetime_format
                )

            if memorial_data["Dates are approximate"] is not None:
                memorial.dates_are_approximate = True

            if not memorial_exists:
                # Add memorial to memorials collection
                try:
                    memorial_index_page.add_child(instance=memorial)
                except AttributeError:
                    print("Could not add memorial as child of memorial index page")

                memorial_index_page.save()
            else:
                memorial.save()
