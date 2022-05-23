# Regex to get CiviCRM ID from parentheses in contact name
# https://stackoverflow.com/a/38999572/1191545

import csv
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from contact.models import (
    Meeting,
    MeetingIndexPage,
    MeetingWorshipTime,
    Organization,
    OrganizationIndexPage,
)


def add_meeting_worship_times(meeting, contact):
    # For a given Meeting model instance,
    # add meeting time(s) from CiviCRM contact data

    if contact["Regular time of Worship on First Day (1)"] != "":
        worship_time = MeetingWorshipTime(
            meeting=meeting,
            worship_type="first_day_worship",
            worship_time=contact["Regular time of Worship on First Day (1)"],
        )

        worship_time.save()

    if contact["Regular time of Worship on First Day (2)"] != "":
        worship_time = MeetingWorshipTime(
            meeting=meeting,
            worship_type="first_day_worship_2nd",
            worship_time=contact["Regular time of Worship on First Day (2)"],
        )

        worship_time.save()

    if (
        contact[
            "Regular day and time of Meeting for Worship on the Occassion of Business"
        ]
        != ""
    ):
        worship_time = MeetingWorshipTime(
            meeting=meeting,
            worship_type="business_meeting",
            worship_time=contact[
                "Regular day and time of Meeting for Worship on the Occassion of Business"
            ],
        )

        worship_time.save()

    if (
        contact["Regular day and time of other weekly or monthly public meetings (1)"]
        != ""
    ):
        worship_time = MeetingWorshipTime(
            meeting=meeting,
            worship_type="other_regular_meeting",
            worship_time=contact[
                "Regular day and time of other weekly or monthly public meetings (1)"
            ],
        )

        worship_time.save()


def determine_meeting_type(contact_type):
    # Meeting Subtypes include
    # - Monthly_Meeting_Worship_Group
    # - Quarterly_Regional_Meeting
    # - Yearly_Meeting
    # - Worship_Group
    #
    # Each contact suptype is mapped
    # to a corresponding Meeting type

    meeting_types = {
        "Yearly_Meeting": "yearly_meeting",
        "Quarterly_Regional_Meeting": "quarterly_meeting",
        "Monthly_Meeting_Worship_Group": "monthly_meeting",
        "Worship_Group": "worship_group",
    }

    return meeting_types[contact_type]


class Command(BaseCommand):
    help = "Import Community Directory from Drupal site"

    def add_arguments(self, parser):
        parser.add_argument("--file", action="store", type=str)

    def handle(self, *args, **options):
        with open(options["file"]) as import_file:
            # Get index pages for use when saving entities
            meeting_index_page = MeetingIndexPage.objects.get()
            organization_index_page = OrganizationIndexPage.objects.get()

            contacts = csv.DictReader(import_file)

            for contact in contacts:
                # Check for entity type among:
                # - Meeting
                # - Organization
                #
                # Contact Subtypes include
                # - Monthly_Meeting_Worship_Group
                # - Quarterly_Regional_Meeting
                # - Yearly_Meeting
                # - Worship_Group
                # - Quaker_Organization
                # - NULL

                contact_type = contact["Contact Subtype"].strip()

                # Most of the contacts are meetings.
                # We will need nested logic to label the meeting based on type.
                meeting_types = [
                    "Yearly_Meeting",
                    "Quarterly_Regional_Meeting",
                    "Monthly_Meeting_Worship_Group",
                    "Worship_Group",
                ]

                # Organization types contains empty string
                # because contacts without a value
                # are organizations in the spreadsheet
                # Make sure empty string catches the contacts without subtype.
                organization_types = ["Quaker_Organization", ""]

                contact_is_meeting = contact_type in meeting_types
                contact_is_organization = contact_type in organization_types
                organization_name = contact["Organization Name"]
                contact_id = contact["Contact ID"]

                print(organization_name, contact_id)

                if contact_is_meeting:
                    # If meeting exists, update
                    # else create new meeting

                    meeting_exists = Meeting.objects.filter(
                        title=organization_name,
                    ).exists()

                    meeting_type = determine_meeting_type(contact_type)

                    if meeting_exists:
                        try:
                            meeting = Meeting.objects.get(
                                title=organization_name,
                            )
                        except MultipleObjectsReturned:
                            print("Duplicate meeting found for:", organization_name)

                        meeting.meeting_type = meeting_type
                        meeting.website = contact["Website"]
                        meeting.phone = contact["Phone"]
                        meeting.email = contact["Email"]
                        meeting.civicrm_id = contact_id

                        meeting.save()

                        add_meeting_worship_times(meeting, contact)
                    else:
                        meeting = Meeting(
                            title=organization_name,
                            civicrm_id=contact_id,
                            meeting_type=meeting_type,
                            website=contact["Website"],
                            phone=contact["Phone"],
                            email=contact["Email"],
                        )

                        meeting_index_page.add_child(instance=meeting)

                        meeting_index_page.save()

                        add_meeting_worship_times(meeting, contact)
                elif contact_is_organization:
                    # If organization exists, update
                    # else create new organization

                    organization_exists = Organization.objects.filter(
                        title=organization_name,
                    ).exists()

                    if organization_exists:
                        print("organization exists")
                        try:
                            organization = Organization.objects.get(
                                title=organization_name,
                            )
                        except MultipleObjectsReturned:
                            print(
                                "Duplicate organization found for:", organization_name
                            )

                        organization.civicrm_id = contact_id

                        organization.save()
                    else:
                        print("new organization")
                        organization = Organization(
                            title=organization_name,
                            civicrm_id=contact_id,
                        )

                        organization_index_page.add_child(instance=organization)

                        organization_index_page.save()
                else:
                    print(f"Contact type: '{contact_type}'")

        self.stdout.write("All done!")
