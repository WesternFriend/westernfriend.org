import pandas as pd
from django.core.exceptions import ObjectDoesNotExist

from contact.models import Meeting, MeetingAddress


def create_meeting_addresses(meeting: Meeting, row: dict) -> None:
    row_has_mailing_address = row["Mailing-State"] != ""
    row_has_worship_address = row["Worship-State"] != ""

    if row_has_mailing_address:
        mailing_address = MeetingAddress(
            street_address=row["Mailing-Street Address"],
            extended_address=row["Mailing-Supplemental Address 1"],
            locality=row["Mailing-City"],
            region=row["Mailing-State"],
            postal_code=row["Mailing-Postal Code"],
            address_type="mailing",
            page=meeting,
        )

        mailing_address.save()

    if row_has_worship_address:
        latitude = row.get("Worship-Latitude") or None
        longitude = row.get("Worship-Longitude") or None

        worship_address = MeetingAddress(
            street_address=row["Worship-Street Address"],
            extended_address=row["Worship-Supplemental Address 1"],
            locality=row["Worship-City"],
            region=row["Worship-State"],
            postal_code=row["Worship-Postal Code"],
            country=row["Worship-Country"],
            address_type="worship",
            latitude=latitude,
            longitude=longitude,
            page=meeting,
        )

        worship_address.save()


def handle_import_civicrm_addresses(file_name: str) -> None:
    addresses = pd.read_csv(file_name).to_dict("records")

    for row in addresses:
        contact_subtype = row["Contact Subtype"]

        meeting_subtypes = [
            "Monthly_Meeting_Worship_Group",
            "Quarterly_Regional_Meeting",
            "Yearly_Meeting",
            "Worship_Group",
        ]

        if contact_subtype in meeting_subtypes:
            try:
                meeting = Meeting.objects.get(civicrm_id=row["Contact ID"])
            except ObjectDoesNotExist:
                print(f"Could not find contact with CiviCRM ID { row['Contact ID'] }")
                pass

            create_meeting_addresses(meeting, row)
