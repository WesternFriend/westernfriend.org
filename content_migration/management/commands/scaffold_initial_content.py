from django.core.management.base import BaseCommand, CommandError

from wagtail.core.models import Page, Site

from contact.models import MeetingIndexPage, OrganizationIndexPage, PersonIndexPage
from home.models import HomePage
from community.models import (
    CommunityPage,
    CommunityDirectoryIndexPage,
    OnlineWorshipIndexPage,
)
from donations.models import DonatePage
from events.models import EventsIndexPage
from facets.models import (
    AudienceIndexPage,
    FacetIndexPage,
    GenreIndexPage,
    MediumIndexPage,
    TimePeriodIndexPage,
    TopicIndexPage,
)
from forms.models import ContactFormPage
from library.models import LibraryIndexPage
from magazine.models import (
    MagazineDepartmentIndexPage,
    MagazineIndexPage,
    MagazineTagIndexPage,
    DeepArchiveIndexPage,
)
from memorials.models import MemorialIndexPage
from news.models import (
    NewsIndexPage,
    NewsTopicIndexPage,
    NewsTypeIndexPage,
)
from store.models import (
    ProductIndexPage,
    StoreIndexPage,
)
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
        community_page = CommunityPage(title="Community", show_in_menus=True)
        contact_form_page = ContactFormPage(title="Contact", show_in_menus=True)
        donate_page = DonatePage(title="Donate", show_in_menus=True)
        events_page = EventsIndexPage(title="Events")
        library_index_page = LibraryIndexPage(title="Library", show_in_menus=True)
        magazine_index_page = MagazineIndexPage(title="Magazine", show_in_menus=True)
        manage_subscription_page = ManageSubscriptionPage(title="Manage subscription")
        news_index_page = NewsIndexPage(title="News")
        store_index_page = StoreIndexPage(title="Bookstore", show_in_menus=True)
        subscription_index_page = SubscriptionIndexPage(title="Subscribe", show_in_menus=True)

        home_page.add_child(instance=community_page)
        home_page.add_child(instance=contact_form_page)
        home_page.add_child(instance=donate_page)
        home_page.add_child(instance=events_page)
        home_page.add_child(instance=library_index_page)
        home_page.add_child(instance=magazine_index_page)
        home_page.add_child(instance=manage_subscription_page)
        home_page.add_child(instance=news_index_page)
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

        # News section
        news_topic_index_page = NewsTopicIndexPage(title="News topics", slug="topic")
        news_type_index_page = NewsTypeIndexPage(title="News types", slug="type")

        news_index_page.add_child(instance=news_topic_index_page)
        news_index_page.add_child(instance=news_type_index_page)

        news_index_page.save()

        # Community section
        community_directory_index_page = CommunityDirectoryIndexPage(title="Community directories")
        meeting_index_page = MeetingIndexPage(title="Meetings")
        memorial_index_page = MemorialIndexPage(title="Memorials", show_in_menus=True)
        online_worship_index_page = OnlineWorshipIndexPage(title="Online meetings for worship")
        organization_index_page = OrganizationIndexPage(title="Organizations")
        person_index_page = PersonIndexPage(title="People")

        community_page.add_child(instance=community_directory_index_page)
        community_page.add_child(instance=meeting_index_page)
        community_page.add_child(instance=memorial_index_page)
        community_page.add_child(instance=online_worship_index_page)
        community_page.add_child(instance=organization_index_page)
        community_page.add_child(instance=person_index_page)
        community_page.save()

        # Library section
        facet_index_page = FacetIndexPage(title="Facets")

        library_index_page.add_child(instance=facet_index_page)

        # Library facets section
        audience_index_page = AudienceIndexPage(title="Audience")
        genre_index_page = GenreIndexPage(title="Genre")
        medium_index_page = MediumIndexPage(title="Medium")
        time_period_index_page = TimePeriodIndexPage(title="Time period")
        topic_index_page = TopicIndexPage(title="Topic")

        facet_index_page.add_child(instance=audience_index_page)
        facet_index_page.add_child(instance=genre_index_page)
        facet_index_page.add_child(instance=medium_index_page)
        facet_index_page.add_child(instance=time_period_index_page)
        facet_index_page.add_child(instance=topic_index_page)

        # Bookstore section
        product_index_page = ProductIndexPage(title="Products")

        store_index_page.add_child(instance=product_index_page)

        self.stdout.write("All done!")
