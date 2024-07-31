from django.core.management.base import BaseCommand
from wagtail.models import Page, Site
from wagtail.blocks import StreamBlock, StreamValue
from documents.models import MeetingDocumentIndexPage, PublicBoardDocumentIndexPage

from community.models import (
    CommunityDirectoryIndexPage,
    CommunityPage,
    OnlineWorshipIndexPage,
)
from contact.models import MeetingIndexPage, OrganizationIndexPage, PersonIndexPage
from events.models import EventsIndexPage
from facets.models import (
    AudienceIndexPage,
    FacetIndexPage,
    GenreIndexPage,
    MediumIndexPage,
    TimePeriodIndexPage,
    TopicIndexPage,
)
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
    NavigationExternalLinkBlock,
    NavigationPageChooserBlock,
)
from news.models import NewsIndexPage
from store.models import ProductIndexPage, StoreIndexPage
from subscription.models import ManageSubscriptionPage, SubscriptionIndexPage
from wf_pages.models import MollyWingateBlogIndexPage, WfPage


def get_or_create_site_root_page() -> Page:
    root_page: Page
    try:
        root_page = Page.objects.get(
            id=1,
        )
    except Page.DoesNotExist:
        root_page = Page.objects.create(
            id=1,
        ).save()

    return root_page


class Command(BaseCommand):
    help = "Create initial site structure"

    def handle(self, *args: tuple, **options: dict[str, str]) -> None:
        root_page = get_or_create_site_root_page()

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
        help_wanted_page = WfPage(
            title="Help Wanted",
            show_in_menus=True,
        )
        future_issues_page = WfPage(
            title="Future Issues",
            show_in_menus=True,
        )
        mission_and_history_page = WfPage(
            title="Mission & History",
            show_in_menus=True,
        )
        board_of_directors_page = WfPage(
            title="Board of Directors",
            show_in_menus=True,
        )
        community_page = CommunityPage(
            title="Community",
            show_in_menus=True,
        )
        events_page = EventsIndexPage(
            title="Events",
            show_in_menus=True,
        )
        library_index_page = LibraryIndexPage(
            title="Library / Media",
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
            show_in_menus=True,
        )
        store_index_page = StoreIndexPage(
            title="Bookstore",
            show_in_menus=True,
        )
        subscription_index_page = SubscriptionIndexPage(
            title="Subscribe",
            show_in_menus=True,
        )
        subscribe_newsletter_page = WfPage(
            title="Subscribe - Newsletter",
            show_in_menus=True,
        )
        podcast_index_page = WfPage(
            title="Podcasts",
            show_in_menus=True,
        )
        public_board_documents_index_page = PublicBoardDocumentIndexPage(
            title="Board Documents",
        )
        meeting_documents_index_page = MeetingDocumentIndexPage(
            title="Meeting Documents",
        )
        molly_wingate_blog_index_page = MollyWingateBlogIndexPage(
            title="Molly Wingate Blog",
        )

        home_page.add_child(instance=community_page)
        home_page.add_child(instance=events_page)
        home_page.add_child(instance=library_index_page)
        home_page.add_child(instance=magazine_index_page)
        home_page.add_child(instance=manage_subscription_page)
        home_page.add_child(instance=news_index_page)
        home_page.add_child(instance=store_index_page)
        home_page.add_child(instance=subscription_index_page)
        home_page.add_child(instance=future_issues_page)
        home_page.add_child(instance=mission_and_history_page)
        home_page.add_child(instance=board_of_directors_page)
        home_page.add_child(instance=help_wanted_page)
        home_page.add_child(instance=subscribe_newsletter_page)
        home_page.add_child(instance=podcast_index_page)
        home_page.add_child(instance=public_board_documents_index_page)
        home_page.add_child(instance=meeting_documents_index_page)
        home_page.add_child(instance=molly_wingate_blog_index_page)

        home_page.save()

        # Magazine section
        magazine_department_index_page = MagazineDepartmentIndexPage(
            title="Departments",
        )
        magazine_tag_index_page = MagazineTagIndexPage(
            title="Tags",
        )
        deep_archive_index_page = DeepArchiveIndexPage(
            title="Deep Archive",
        )

        magazine_index_page.add_child(instance=magazine_department_index_page)
        magazine_index_page.add_child(instance=magazine_tag_index_page)
        magazine_index_page.add_child(instance=deep_archive_index_page)

        magazine_index_page.save()

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

        mock_menu_block = StreamBlock(
            [
                ("page", NavigationPageChooserBlock()),
                ("external_link", NavigationExternalLinkBlock()),
            ],
        )

        magazine_books_dropdown = {
            "title": "Magazine / Books",
            # StreamBlock
            "menu_items": StreamValue(
                stream_block=mock_menu_block,
                stream_data=[
                    (
                        "page",
                        {
                            "title": "Recent Issues",
                            "page": magazine_index_page,
                        },
                    ),
                    (
                        "page",
                        {
                            "title": "Archive Issues",
                            "page": deep_archive_index_page,
                        },
                    ),
                    (
                        "page",
                        {
                            "title": "Future Issues",
                            "page": future_issues_page,
                        },
                    ),
                    (
                        "page",
                        {
                            "title": "Books",
                            "page": store_index_page,
                        },
                    ),
                ],
            ),
        }

        other_content_dropdown = {
            "title": "Other Content",
            # StreamBlock
            "menu_items": StreamValue(
                stream_block=mock_menu_block,
                stream_data=[
                    (
                        "page",
                        {
                            "title": "Library / Media",
                            "page": library_index_page,
                        },
                    ),
                    (
                        "page",
                        {
                            "title": "Extra Extra / News",
                            "page": news_index_page,
                        },
                    ),
                    # TODO: create PodcastIndexPage / feature
                    (
                        "page",
                        {
                            "title": "Podcasts",
                            "page": podcast_index_page,
                        },
                    ),
                    (
                        "page",
                        {
                            "title": "Memorials",
                            "page": memorial_index_page,
                        },
                    ),
                ],
            ),
        }

        about_us_dropdown = {
            "title": "About Us",
            # StreamBlock
            "menu_items": StreamValue(
                stream_block=mock_menu_block,
                stream_data=[
                    (
                        "page",
                        {
                            "title": "Mission & History",
                            "page": mission_and_history_page,
                        },
                    ),
                    (
                        "page",
                        {
                            "title": "Board of Directors",
                            "page": board_of_directors_page,
                        },
                    ),
                    (
                        "page",
                        {
                            "title": "Directories",
                            "page": community_directory_index_page,
                        },
                    ),
                ],
            ),
        }

        events_dropdown = {
            "title": "Events",
            # StreamBlock
            "menu_items": StreamValue(
                stream_block=mock_menu_block,
                stream_data=[
                    (
                        "page",
                        {
                            "title": "Online Worship",
                            "page": online_worship_index_page,
                        },
                    ),
                    (
                        "page",
                        {
                            "title": "Western Events",
                            "page": events_page,
                        },
                    ),
                    (
                        "external_link",
                        {
                            "title": "Other Events",
                            "url": f"{events_page.relative_url(current_site=site)}?category=other",  # noqa: E501
                        },
                    ),
                ],
            ),
        }

        subscribe_dropdown = {
            "title": "Subscribe",
            # StreamBlock
            "menu_items": StreamValue(
                stream_block=mock_menu_block,
                stream_data=[
                    (
                        "page",
                        {
                            "title": "Subscribe - Magazine",
                            "page": subscription_index_page,
                        },
                    ),
                    (
                        "page",
                        {
                            "title": "Subscribe - Newsletter",
                            "page": subscribe_newsletter_page,
                        },
                    ),
                    (
                        "page",
                        {
                            "title": "Help Wanted",
                            "page": help_wanted_page,
                        },
                    ),
                ],
            ),
        }

        # Navigation menu
        navigation_items = [
            ("drop_down", magazine_books_dropdown),
            ("drop_down", other_content_dropdown),
            ("drop_down", about_us_dropdown),
            ("drop_down", events_dropdown),
            ("drop_down", subscribe_dropdown),
        ]
        navigation_menu = _get_or_create_navigation_menu_setting()

        navigation_menu.menu_items = navigation_items

        navigation_menu.save()

        self.stdout.write("All done!")


def _get_or_create_navigation_menu_setting() -> NavigationMenuSetting:
    site = Site.objects.get(id=1)
    try:
        navigation_menu = NavigationMenuSetting.objects.get(site_id=site.id)
    except NavigationMenuSetting.DoesNotExist:
        navigation_menu = NavigationMenuSetting(
            site_id=site.id,
        )
        navigation_menu.save()
    return navigation_menu
