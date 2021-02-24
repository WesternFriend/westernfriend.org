from django.core.management.base import BaseCommand, CommandError

from wagtail.core.models import Page, Site

from contact.models import MeetingIndexPage, OrganizationIndexPage, PersonIndexPage
from home.models import HomePage
from community.models import CommunityPage
from donations.models import DonatePage
from events.models import EventsIndexPage
from forms.models import ContactFormPage
from library.models import LibraryIndexPage
from magazine.models import (
    MagazineDepartmentIndexPage,
    MagazineIndexPage,
    MagazineTagIndexPage,
    DeepArchiveIndexPage,
)
from store.models import StoreIndexPage
from subscription.models import (
    SubscriptionIndexPage,
    ManageSubscriptionPage,
)



class Command(BaseCommand):
    help = "Create initial site structure"

    def handle(self, *args, **options):
        root_page = Page.objects.get(id=1)
        home_page = HomePage(title="Welcome")

        root_page.add_child(instance=home_page)
        root_page.save()

        # Set Home Page as root page for Site
        site = Site.objects.get(id=1)
        site.root_page = home_page
        site.save()

        # Delete welcome page
        # ID: 2 is used, since welcome page is second page created
        # Otherwise, the title "Welcome to your new Wagtail site!" might be useful
        Page.objects.get(id=2).delete()

        # Create Home Page children
        community_page = CommunityPage(title="Community")
        contact_form_page = ContactFormPage(title="Contact")
        donate_page = DonatePage(title="Donate")
        events_page = EventsIndexPage(title="Events")
        library_index_page = LibraryIndexPage(title="Library")
        magazine_index_page = MagazineIndexPage(title="Magazine")
        manage_subscription_page = ManageSubscriptionPage(title="Manage subscription")
        store_index_page = StoreIndexPage(title="Bookstore")
        subscription_index_page = SubscriptionIndexPage(title="Subscribe")

        home_page.add_child(instance=community_page)
        home_page.add_child(instance=contact_form_page)
        home_page.add_child(instance=donate_page)
        home_page.add_child(instance=events_page)
        home_page.add_child(instance=library_index_page)
        home_page.add_child(instance=magazine_index_page)
        home_page.add_child(instance=manage_subscription_page)
        home_page.add_child(instance=store_index_page)
        home_page.add_child(instance=subscription_index_page)
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
