from django.core.management.base import BaseCommand, CommandError

from wagtail.core.models import Page

from contact.models import MeetingIndexPage, OrganizationIndexPage, PersonIndexPage
from home.models import HomePage
from community.models import CommunityPage
from magazine.models import (
    MagazineDepartmentIndexPage,
    MagazineIndexPage,
    MagazineTagIndexPage,
    DeepArchiveIndexPage,
)


class Command(BaseCommand):
    help = "Create initial site structure"

    def handle(self, *args, **options):
        root_page = Page.objects.get(id=1)
        home_page = HomePage(title="Welcome")

        root_page.add_child(instance=home_page)
        root_page.save()

        community_page = CommunityPage(title="Community")
        magazine_index_page = MagazineIndexPage(title="Magazine")

        home_page.add_child(instance=community_page)
        home_page.add_child(instance=magazine_index_page)
        home_page.save()

        # Magazine section
        magazine_department_index_page = MagazineDepartmentIndexPage(
            title="Departments"
        )
        magazine_tag_index_page = MagazineTagIndexPage(title="Tags")
        deep_archive_index_page = DeepArchiveIndexPage(title="Archive")

        magazine_index_page.add_child(instance=magazine_department_index_page)
        magazine_index_page.add_child(instance=magazine_tag_index_page)
        magazine_index_page.add_child(instance=deep_archive_index_page)

        magazine_index_page.save()

        # Community section
        meeting_index_page = MeetingIndexPage(title="Meetings")
        organization_index_page = OrganizationIndexPage(title="Organizations")
        person_index_page = PersonIndexPage(title="People")

        community_page.add_child(instance=meeting_index_page)
        community_page.add_child(instance=organization_index_page)
        community_page.add_child(instance=person_index_page)
        community_page.save()

        self.stdout.write("All done!")
