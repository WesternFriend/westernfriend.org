import logging

from tqdm import tqdm

from contact.models import (
    Meeting,
    MeetingIndexPage,
    Organization,
    OrganizationIndexPage,
    Person,
    PersonIndexPage,
)
from content_migration.management.shared import parse_csv_file

logging.basicConfig(
    filename="import_log_magazine_authors.log",
    level=logging.ERROR,
    format="%(message)s",
    # format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def create_meeting(
    author: dict,
    meeting_index_page: MeetingIndexPage,
) -> None:
    # check if meeting already exists
    # if it does, update it
    # if it doesn't, create it
    meeting_exists = Meeting.objects.filter(
        drupal_author_id=author["drupal_author_id"]
    ).exists()

    if meeting_exists:
        meeting = Meeting.objects.get(
            drupal_author_id=author["drupal_author_id"],
        )

        meeting.title = author["drupal_full_name"]
        meeting.civicrm_id = (
            author["civicrm_contact_id"] if author["civicrm_contact_id"] != "" else None
        )

        meeting.save()
    else:
        meeting = Meeting(
            title=author["drupal_full_name"],
            drupal_author_id=author["drupal_author_id"],
            civicrm_id=author["civicrm_contact_id"]
            if author["civicrm_contact_id"] != ""
            else None,
        )

        meeting_index_page.add_child(instance=meeting)

        meeting_index_page.save()


def create_organization(
    author: dict,
    organization_index_page: OrganizationIndexPage,
) -> None:
    organization_exists = Organization.objects.filter(
        drupal_author_id=author["drupal_author_id"]
    ).exists()

    if organization_exists:
        organization = Organization.objects.get(
            drupal_author_id=author["drupal_author_id"],
        )

        organization.title = author["drupal_full_name"]
        organization.civicrm_id = (
            author["civicrm_contact_id"] if author["civicrm_contact_id"] != "" else None
        )

        organization.save()
    else:
        organization = Organization(
            title=author["drupal_full_name"],
            drupal_author_id=author["drupal_author_id"],
            civicrm_id=author["civicrm_contact_id"]
            if author["civicrm_contact_id"] != ""
            else None,
        )

        organization_index_page.add_child(instance=organization)

        organization_index_page.save()


def create_person(
    author: dict,
    person_index_page: PersonIndexPage,
) -> None:
    person_exists = Person.objects.filter(
        drupal_author_id=author["drupal_author_id"]
    ).exists()

    if person_exists:
        person = Person.objects.get(
            drupal_author_id=author["drupal_author_id"],
        )

        person.given_name = author["given_name"]
        person.family_name = author["family_name"]
        person.civicrm_id = (
            author["civicrm_contact_id"] if author["civicrm_contact_id"] != "" else None
        )

        person.save()
    else:
        person = Person(
            given_name=author["given_name"],
            family_name=author["family_name"],
            drupal_author_id=author["drupal_author_id"],
            civicrm_id=author["civicrm_contact_id"]
            if author["civicrm_contact_id"] != ""
            else None,
        )

        person_index_page.add_child(instance=person)

        person_index_page.save()


def import_author_records(authors_list: list[dict]) -> None:
    meeting_index_page = MeetingIndexPage.objects.get()
    organization_index_page = OrganizationIndexPage.objects.get()
    person_index_page = PersonIndexPage.objects.get()

    if not meeting_index_page or not organization_index_page or not person_index_page:
        raise Exception("Could not find author index pages")

    for author in tqdm(
        authors_list,
        desc="Primary Author records",
        unit="row",
    ):
        author_type = author["author_type"]

        # Don't import duplicate authors
        # Instead, clean them up in the Drupal site
        if author["duplicate_of_id"] != "":
            logger.warning(
                f"Author { author['drupal_author_id'] } is marked as a duplicate"
            )

            # continue to next author record
            continue
        else:
            if author_type == "meeting":
                create_meeting(author, meeting_index_page)
            elif author_type == "organization":
                create_organization(author, organization_index_page)
            elif author_type == "person":
                create_person(author, person_index_page)
            else:
                logger.error(
                    f"Unknown author type for ID: { author['drupal_author_id'] }"
                )


def handle_import_magazine_authors(file_name: str) -> None:
    authors_list = parse_csv_file(file_name)

    import_author_records(authors_list)
