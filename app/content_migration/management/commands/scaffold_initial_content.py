from django.core.management.base import BaseCommand, CommandError
from wagtail import blocks as wagtail_blocks
from wagtail.models import Page, Site
from wagtail.blocks import StreamBlock, StreamValue

from community.models import (
    CommunityDirectoryIndexPage,
    CommunityPage,
    OnlineWorshipIndexPage,
)
from contact.models import MeetingIndexPage, OrganizationIndexPage, PersonIndexPage
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
from home.models import HomePage
from library.models import LibraryIndexPage
from magazine.models import (
    DeepArchiveIndexPage,
    MagazineDepartmentIndexPage,
    MagazineIndexPage,
    MagazineTagIndexPage,
)
from memorials.models import MemorialIndexPage
from navigation.models import NavigationMenuSetting
from navigation.blocks import (
    NavigationDropdownMenuBlock,
    NavigationPageChooserBlock,
)
from news.models import NewsIndexPage, NewsTopicIndexPage, NewsTypeIndexPage
from store.models import ProductIndexPage, StoreIndexPage
from subscription.models import ManageSubscriptionPage, SubscriptionIndexPage
from wf_pages.models import WfPage


class Command(BaseCommand):
    help = "Create initial site structure"

    def handle(self, *args, **options):
        try:
            root_page = Page.objects.get(id=1)
        except Page.DoesNotExist:
            root_page = Page(id=1).save()

        home_page = HomePage(
            title="Welcome",
        )

        root_page.add_child(instance=home_page)
        root_page.save()

        # Set Home Page as root page for Site
        site = Site.objects.get(id=1)
        site.root_page = home_page
        site.save()

        # Delete welcome page
        # ID: 2 is used, since welcome page is second page created
        # Otherwise, the title "Welcome to your new Wagtail site!" might be useful
        try:
            Page.objects.get(id=2).delete()
        except Page.DoesNotExist:
            print("No need to delete welcome page")

        # Create Home Page children

        # Custom WF Pages in site root
        help_wanted = WfPage(
            title="Help Wanted",
        )
        future_issues = WfPage(
            title="Future Issues",
        )
        mission_and_history = WfPage(
            title="Mission & History",
        )
        board_of_directors = WfPage(
            title="Board of Directors",
        )
        community_page = CommunityPage(
            title="Community",
            show_in_menus=True,
        )
        contact_form_page = ContactFormPage(
            title="Contact",
            show_in_menus=True,
        )
        donate_page = DonatePage(
            title="Donate",
            show_in_menus=True,
        )
        events_page = EventsIndexPage(
            title="Events",
        )
        library_index_page = LibraryIndexPage(
            title="Library",
            show_in_menus=True,
        )
        magazine_index_page = MagazineIndexPage(
            title="Magazine",
            show_in_menus=True,
        )
        manage_subscription_page = ManageSubscriptionPage(
            title="Manage subscription",
        )
        news_index_page = NewsIndexPage(
            title="News",
        )
        store_index_page = StoreIndexPage(
            title="Bookstore",
            show_in_menus=True,
        )
        subscription_index_page = SubscriptionIndexPage(
            title="Subscribe",
            show_in_menus=True,
        )

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
        home_page.add_child(instance=future_issues)
        home_page.add_child(instance=mission_and_history)
        home_page.add_child(instance=board_of_directors)
        home_page.add_child(instance=help_wanted)
        home_page.save()

        # Magazine section
        magazine_department_index_page = MagazineDepartmentIndexPage(
            title="Departments",
        )
        magazine_tag_index_page = MagazineTagIndexPage(
            title="Tags",
        )
        deep_archive_index_page = DeepArchiveIndexPage(
            title="Archive",
        )

        magazine_index_page.add_child(instance=magazine_department_index_page)
        magazine_index_page.add_child(instance=magazine_tag_index_page)
        magazine_index_page.add_child(instance=deep_archive_index_page)

        magazine_index_page.save()

        # News section
        news_topic_index_page = NewsTopicIndexPage(
            title="News topics",
            slug="topic",
        )
        news_type_index_page = NewsTypeIndexPage(
            title="News types",
            slug="type",
        )

        news_index_page.add_child(instance=news_topic_index_page)
        news_index_page.add_child(instance=news_type_index_page)

        news_index_page.save()

        # Community section
        community_directory_index_page = CommunityDirectoryIndexPage(
            title="Community directories",
        )
        meeting_index_page = MeetingIndexPage(
            title="Meetings",
        )
        memorial_index_page = MemorialIndexPage(
            title="Memorials",
            show_in_menus=True,
        )
        online_worship_index_page = OnlineWorshipIndexPage(
            title="Online meetings for worship",
        )
        organization_index_page = OrganizationIndexPage(
            title="Organizations",
        )
        person_index_page = PersonIndexPage(
            title="People",
        )

        community_page.add_child(instance=community_directory_index_page)
        community_page.add_child(instance=meeting_index_page)
        community_page.add_child(instance=memorial_index_page)
        community_page.add_child(instance=online_worship_index_page)
        community_page.add_child(instance=organization_index_page)
        community_page.add_child(instance=person_index_page)
        community_page.save()

        # Library section
        facet_index_page = FacetIndexPage(
            title="Facets",
        )

        library_index_page.add_child(instance=facet_index_page)

        # Library facets section
        audience_index_page = AudienceIndexPage(
            title="Audience",
        )
        genre_index_page = GenreIndexPage(
            title="Genre",
        )
        medium_index_page = MediumIndexPage(
            title="Medium",
        )
        time_period_index_page = TimePeriodIndexPage(
            title="Time period",
        )
        topic_index_page = TopicIndexPage(
            title="Topic",
        )

        facet_index_page.add_child(instance=audience_index_page)
        facet_index_page.add_child(instance=genre_index_page)
        facet_index_page.add_child(instance=medium_index_page)
        facet_index_page.add_child(instance=time_period_index_page)
        facet_index_page.add_child(instance=topic_index_page)

        # Bookstore section
        product_index_page = ProductIndexPage(
            title="Products",
        )

        store_index_page.add_child(instance=product_index_page)

        magazine_page_menu_item_value = {
            "title": "Magazine",
            "page": magazine_index_page,
        }

        stream_data = [
            {
                "type": "page",
                # StructBlock
                "value": magazine_page_menu_item_value,
            },
        ]

        magazine_books_dropdown = {
            "title": "Magazine / Books",
            # StreamBlock
            "menu_items": StreamValue(
                # TODO: determine how to tell this StreamValue what
                # type of block to use.....
                # https://stackoverflow.com/questions/75548482/how-to-programatically-create-a-wagtail-structblock-containing-a-streamfield
                # https://stackoverflow.com/questions/46795866/add-streamblock-child-items-programmatically-in-wagtail?rq=1
                stream_block=NavigationPageChooserBlock(),
                stream_data=stream_data,
            ),
        }

        # ("page", deep_archive_index_page),
        # ("page", future_issues),
        # ("page", store_index_page),

        # Navigation menu
        navigation_items = [
            ("drop_down", magazine_books_dropdown),
        ]
        navigation_menu = NavigationMenuSetting(
            menu_items=navigation_items,
            site_id=1,
        )

        navigation_menu.save()

        self.stdout.write("All done!")
