"""Build a complete, realistic content tree for local development.

The work is split between two layers:

- The app factories (``<app>/factories.py``) own every field value. They
  declare Faker defaults and traits for the variations the site needs to
  show, such as ``EventFactory(past=True)`` or ``BookFactory(sold_out=True)``.
- This seeder owns the site's shape: how many of each thing, where each page
  sits in the tree, how pages relate (authors, sponsors, clerks, topics), and
  the publication schedule that puts some magazine issues behind the paywall.

Pages are built with ``Factory.build()`` and attached with
``parent.add_child()``, so the same factories keep working unchanged in tests.
"""

import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import factory.random
from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from wagtail.models import Page, PageViewRestriction

from accounts.factories import UserFactory
from common import fake_content
from common.fake_content import fake
from community.factories import CommunityDirectoryFactory, OnlineWorshipFactory
from community.models import (
    CommunityDirectoryIndexPage,
    CommunityPage,
    OnlineWorshipIndexPage,
)
from contact.factories import (
    MeetingFactory,
    MeetingPresidingClerkFactory,
    OrganizationFactory,
    PersonFactory,
)
from contact.models import (
    Meeting,
    MeetingIndexPage,
    Organization,
    OrganizationIndexPage,
    Person,
    PersonIndexPage,
)
from documents.factories import MeetingDocumentFactory, PublicBoardDocumentFactory
from documents.models import (
    MeetingDocumentIndexPage,
    PublicBoardDocument,
    PublicBoardDocumentIndexPage,
)
from events.factories import EventFactory
from events.models import EventsIndexPage, EventSponsor
from facets.factories import (
    AudienceFactory,
    GenreFactory,
    MediumFactory,
    TimePeriodFactory,
    TopicFactory,
)
from facets.models import (
    AudienceIndexPage,
    GenreIndexPage,
    MediumIndexPage,
    TimePeriodIndexPage,
    TopicIndexPage,
)
from home.models import HomePage
from library.factories import LibraryItemFactory
from library.models import LibraryIndexPage, LibraryItemAuthor, LibraryItemTopic
from magazine.factories import (
    ArchiveArticleAuthorFactory,
    ArchiveIssueFactory,
    MagazineArticleAuthorFactory,
    MagazineArticleFactory,
    MagazineDepartmentFactory,
    MagazineIssueFactory,
)
from magazine.models import (
    DeepArchiveIndexPage,
    MagazineDepartmentIndexPage,
    MagazineIndexPage,
)
from memorials.factories import MemorialFactory
from memorials.models import MemorialIndexPage
from news.factories import NewsItemFactory
from news.models import NewsIndexPage, NewsItemTopic
from orders.factories import OrderFactory, OrderItemFactory
from store.factories import BookAuthorFactory, BookFactory
from store.models import ProductIndexPage, StoreIndexPage
from subscription.models import (
    ManageSubscriptionPage,
    Subscription,
    SubscriptionIndexPage,
)
from wf_pages.factories import (
    MollyWingateBlogPageFactory,
    WfPageCollectionFactory,
    WfPageFactory,
)
from wf_pages.models import (
    MollyWingateBlogIndexPage,
    WfPage,
    WfPageCollectionIndexPage,
)

from . import images

# Accounts are only created when missing, and ``--reset`` removes exactly
# these. The shared password is for local development only.
DEV_PASSWORD = "westernfriend-dev"  # noqa: S105
DEV_USERS = {
    "admin": f"admin@{fake_content.EMAIL_DOMAIN}",
    "subscriber": f"subscriber@{fake_content.EMAIL_DOMAIN}",
    "expired": f"expired-subscriber@{fake_content.EMAIL_DOMAIN}",
    "reader": f"reader@{fake_content.EMAIL_DOMAIN}",
}


# The home page shows three featured events; the bookstore leads with
# its featured books.
FEATURED_EVENTS = 3
FEATURED_BOOKS = 2


def _in_share(number: int, share: int, out_of: int) -> bool:
    """Whether item ``number`` falls in a repeating share, e.g. 3 of every 5."""
    return number % out_of < share


@dataclass(frozen=True)
class Scale:
    people: int
    organizations: int
    yearly_meetings: int
    quarterly_per_yearly: int
    monthly_per_quarterly: int
    online_worship: int
    directories: int
    memorials: int
    library_items: int
    magazine_issues: int
    articles_per_issue: tuple[int, int]
    archive_issues: int
    events: int
    news_items: int
    books: int
    orders: int
    meeting_documents: int
    blog_posts: int
    collections: int
    illustrations: int


SCALES = {
    "small": Scale(
        people=24,
        organizations=4,
        yearly_meetings=2,
        quarterly_per_yearly=1,
        monthly_per_quarterly=2,
        online_worship=4,
        directories=3,
        memorials=4,
        library_items=12,
        magazine_issues=6,
        articles_per_issue=(3, 4),
        archive_issues=4,
        events=8,
        news_items=8,
        books=6,
        orders=3,
        meeting_documents=4,
        blog_posts=3,
        collections=2,
        illustrations=4,
    ),
    "medium": Scale(
        people=90,
        organizations=12,
        yearly_meetings=3,
        quarterly_per_yearly=2,
        monthly_per_quarterly=3,
        online_worship=12,
        directories=6,
        memorials=20,
        library_items=60,
        magazine_issues=18,
        articles_per_issue=(6, 10),
        archive_issues=24,
        events=30,
        news_items=40,
        books=20,
        orders=12,
        meeting_documents=16,
        blog_posts=10,
        collections=3,
        illustrations=12,
    ),
    "large": Scale(
        people=300,
        organizations=30,
        yearly_meetings=5,
        quarterly_per_yearly=3,
        monthly_per_quarterly=4,
        online_worship=40,
        directories=10,
        memorials=80,
        library_items=300,
        magazine_issues=48,
        articles_per_issue=(8, 12),
        archive_issues=80,
        events=120,
        news_items=150,
        books=60,
        orders=50,
        meeting_documents=60,
        blog_posts=30,
        collections=5,
        illustrations=24,
    ),
}


class DevContentSeeder:
    def __init__(
        self,
        *,
        scale: Scale,
        seed: int,
        with_images: bool,
        log: Callable[[str], None] = lambda _message: None,
    ) -> None:
        self.scale = scale
        self.with_images = with_images
        self.log = log

        # Faker's shared generator (used by factory_boy and fake_content)
        # and the stdlib random module (used by some factories) both follow
        # this seed, so a given seed rebuilds the same site on the same day.
        factory.random.reseed_random(seed)
        random.seed(seed)

        self.today = timezone.localdate()
        self.counts: dict[str, int] = {}
        self._sibling_slugs: dict[str, set[str]] = {}

        self.illustrations: list[Any] = []
        self.link_pages: list[Page] = []
        self.people: list[Person] = []
        self.meetings: list[Meeting] = []
        self.monthly_meetings: list[Meeting] = []
        self.organizations: list[Organization] = []

    # Helpers

    def _count(self, label: str, amount: int = 1) -> None:
        self.counts[label] = self.counts.get(label, 0) + amount

    def _unique_slug(self, parent: Page, title: str) -> str:
        taken = self._sibling_slugs.get(parent.path)
        if taken is None:
            taken = set(parent.get_children().values_list("slug", flat=True))
            self._sibling_slugs[parent.path] = taken

        base = (slugify(title) or "page")[:200]
        slug, suffix = base, 2
        while slug in taken:
            slug = f"{base}-{suffix}"
            suffix += 1
        taken.add(slug)
        return slug

    def _add(self, parent: Page, page: Page, *, live: bool = True) -> Page:
        """Attach ``page`` under ``parent`` as a published page or a draft.

        Factories give pages placeholder slugs; here each gets a readable
        slug from its title. Pages skip the revision-then-publish round
        trip, which re-saves and re-indexes every page and triples seeding
        time; drafts still get a revision so the admin shows them properly.
        """
        page.slug = self._unique_slug(parent, page.title)
        page.live = live
        if live:
            page.first_published_at = page.last_published_at = timezone.now()
        parent.add_child(instance=page)
        if not live:
            page.save_revision(log_action=False)
        self._count(type(page)._meta.verbose_name_plural)
        return page

    def _update(self, page: Page, **fields: Any) -> None:
        """Set fields on a scaffolded page."""
        for name, value in fields.items():
            setattr(page, name, value)
        page.save()

    def _intro(self) -> str:
        return fake_content.rich_text(self.link_pages)

    @property
    def _body_pools(self) -> dict[str, list]:
        """Factory params that let bodies show images and link to pages."""
        return {"body_images": self.illustrations, "body_links": self.link_pages}

    def _image(self, title: str, alt_text: str, size: tuple[int, int]) -> Any:
        if not self.with_images:
            return None
        self._count("images")
        return images.create_image(
            title=title,
            alt_text=alt_text,
            size=size,
            collection=self.collection,
        )

    def _authors(self, count: int) -> list[Page]:
        """Mostly people, occasionally a meeting or organization, as on the live site."""
        authors: list[Page] = list(
            fake.random_elements(self.people, length=count, unique=True),
        )
        if fake.boolean(chance_of_getting_true=10):
            authors[-1] = fake.random_element(self.meetings + self.organizations)
        return authors

    def _some(self, pool: list, low: int, high: int) -> list:
        return list(
            fake.random_elements(pool, length=fake.random_int(low, high), unique=True),
        )

    def _tags(self) -> list[str]:
        return self._some(fake_content.TAGS, 1, 3)

    # Sections

    def run(self) -> dict[str, int]:
        steps = [
            ("images", self.seed_images),
            ("users", self.seed_users),
            ("facets", self.seed_facets),
            ("contacts", self.seed_contacts),
            ("community", self.seed_community),
            ("memorials", self.seed_memorials),
            ("pages", self.seed_wf_pages),
            ("library", self.seed_library),
            ("magazine", self.seed_magazine),
            ("deep archive", self.seed_deep_archive),
            ("events", self.seed_events),
            ("news", self.seed_news),
            ("bookstore", self.seed_bookstore),
            ("documents", self.seed_documents),
            ("subscriptions", self.seed_subscription_pages),
            ("home page", self.seed_home_page),
        ]
        for label, step in steps:
            started = time.monotonic()
            step()
            self.log(f"Seeded {label} in {time.monotonic() - started:.1f}s")
        return self.counts

    def seed_images(self) -> None:
        if not self.with_images:
            return
        self.collection = images.get_seed_collection()
        for _ in range(self.scale.illustrations):
            subject = (
                f"{fake.random_element(fake_content.TITLE_ADJECTIVES)} "
                f"{fake.random_element(fake_content.TITLE_NOUNS)}"
            )
            self.illustrations.append(
                self._image(
                    title=subject,
                    alt_text=f"Illustration titled {subject}",
                    size=images.ILLUSTRATION_SIZE,
                ),
            )

    def seed_users(self) -> None:
        user_model = get_user_model()
        existing = set(
            user_model.objects.filter(email__in=DEV_USERS.values()).values_list(
                "email",
                flat=True,
            ),
        )

        def make(key: str, **fields: Any) -> Any:
            email = DEV_USERS[key]
            if email in existing:
                return None
            user = UserFactory.build(
                **{
                    "email": email,
                    "first_name": fake.first_name(),
                    "last_name": fake.last_name(),
                    "is_active": True,
                    "is_staff": False,
                    **fields,
                },
            )
            user.set_password(DEV_PASSWORD)
            user.save()
            self._count("users")
            return user

        make("admin", is_staff=True, is_superuser=True)
        make("reader")

        # PayPal-managed subscriptions call PayPal to check status, so dev
        # subscriptions use only an expiration date.
        subscriber = make("subscriber")
        if subscriber:
            Subscription.objects.create(
                user=subscriber,
                expiration_date=self.today + relativedelta(years=1),
            )
        expired = make("expired")
        if expired:
            Subscription.objects.create(
                user=expired,
                expiration_date=self.today - relativedelta(months=2),
            )

    def seed_facets(self) -> None:
        groups = [
            (AudienceIndexPage, AudienceFactory, fake_content.AUDIENCES),
            (GenreIndexPage, GenreFactory, fake_content.GENRES),
            (MediumIndexPage, MediumFactory, fake_content.MEDIA),
            (TimePeriodIndexPage, TimePeriodFactory, fake_content.TIME_PERIODS),
            (TopicIndexPage, TopicFactory, fake_content.TOPICS),
        ]
        self.facets: dict[str, list[Page]] = {}
        for index_model, facet_factory, titles in groups:
            index_page = index_model.objects.get()
            self.facets[index_model.__name__] = [
                self._add(index_page, facet_factory.build(title=title))
                for title in titles
            ]
        self.topics = self.facets["TopicIndexPage"]

    def seed_contacts(self) -> None:
        person_index = PersonIndexPage.objects.get()
        # Non-ASCII names catch encoding and sorting problems.
        for given_name, family_name in fake_content.INTERNATIONAL_NAMES:
            self.people.append(
                self._add(
                    person_index,
                    PersonFactory.build(given_name=given_name, family_name=family_name),
                ),
            )
        for _ in range(self.scale.people - len(self.people)):
            self.people.append(self._add(person_index, PersonFactory.build()))

        organization_index = OrganizationIndexPage.objects.get()
        self.organizations = [
            self._add(organization_index, OrganizationFactory.build())
            for _ in range(self.scale.organizations)
        ]

        # Yearly > quarterly > monthly meetings > worship groups, the
        # hierarchy the meeting directory and contact pages render.
        meeting_index = MeetingIndexPage.objects.get()
        regions = fake_content.YEARLY_MEETING_REGIONS[: self.scale.yearly_meetings]
        for region in regions:
            yearly = self._meeting(
                meeting_index,
                yearly_meeting=True,
                title=f"{region} Yearly Meeting",
            )
            for _ in range(self.scale.quarterly_per_yearly):
                quarterly = self._meeting(yearly, quarterly_meeting=True)
                for _ in range(self.scale.monthly_per_quarterly):
                    monthly = self._meeting(quarterly, monthly_meeting=True)
                    self.monthly_meetings.append(monthly)
                    if fake.boolean():
                        self._meeting(monthly, worship_group=True)

    def _meeting(self, parent: Page, **traits: Any) -> Meeting:
        meeting = MeetingFactory.build(complete=True, **traits)
        meeting.presiding_clerks = [
            MeetingPresidingClerkFactory.build(person=fake.random_element(self.people)),
        ]
        self.meetings.append(self._add(parent, meeting))
        return meeting

    def seed_community(self) -> None:
        online_worship_index = OnlineWorshipIndexPage.objects.get()
        for _ in range(self.scale.online_worship):
            host = fake.random_element(self.monthly_meetings + self.organizations)
            self._add(
                online_worship_index,
                OnlineWorshipFactory.build(
                    title=f"{host.title} Online Worship",
                    hosted_by=host,
                ),
            )

        directory_index = CommunityDirectoryIndexPage.objects.get()
        for _ in range(self.scale.directories):
            self._add(directory_index, CommunityDirectoryFactory.build())

        self._update(online_worship_index, intro=self._intro())
        self._update(directory_index, intro=self._intro())

    def seed_memorials(self) -> None:
        memorial_index = MemorialIndexPage.objects.get()
        # Memorials get their own people, so authors aren't also memorialised.
        person_index = PersonIndexPage.objects.get()
        for _ in range(self.scale.memorials):
            person = self._add(person_index, PersonFactory.build())
            self._add(
                memorial_index,
                MemorialFactory.build(
                    title=person.title,
                    memorial_person=person,
                    memorial_meeting=fake.random_element(self.monthly_meetings),
                ),
            )
        self._update(memorial_index, intro=self._intro())

    def seed_wf_pages(self) -> None:
        home = HomePage.objects.get()

        # Fill the scaffolded standalone pages (Mission & History, etc.).
        for page in WfPage.objects.child_of(home).exact_type(WfPage):
            self._update(page, body=WfPageFactory.build(**self._body_pools).body)
            self.link_pages.append(page)

        collection_index = WfPageCollectionIndexPage.objects.first()
        if collection_index is None:
            collection_index = self._add(
                home,
                WfPageCollectionIndexPage(title="Collections"),
            )
        self._update(collection_index, intro=self._intro())
        for _ in range(self.scale.collections):
            collection = self._add(collection_index, WfPageCollectionFactory.build())
            for _ in range(3):
                page = WfPageFactory.build(collection=collection, **self._body_pools)
                page.tags.add(*self._tags())
                self._add(home, page)

        # A login-only page, for checking how restricted pages behave.
        members_page = self._add(
            home,
            WfPageFactory.build(title="Board Handbook", **self._body_pools),
        )
        PageViewRestriction.objects.create(
            page=members_page,
            restriction_type=PageViewRestriction.LOGIN,
        )

        blog_index = MollyWingateBlogIndexPage.objects.get()
        for _ in range(self.scale.blog_posts):
            self._add(blog_index, MollyWingateBlogPageFactory.build(**self._body_pools))
        self._update(blog_index, intro=self._intro())

    def seed_library(self) -> None:
        library_index = LibraryIndexPage.objects.get()
        facet_fields = {
            "item_audience": self.facets["AudienceIndexPage"],
            "item_genre": self.facets["GenreIndexPage"],
            "item_medium": self.facets["MediumIndexPage"],
            "item_time_period": self.facets["TimePeriodIndexPage"],
        }
        # The first item has no facets, authors, or topics, to cover the
        # sparse layout.
        self._add(library_index, LibraryItemFactory.build(**self._body_pools))
        for _ in range(self.scale.library_items - 1):
            item = LibraryItemFactory.build(
                **self._body_pools,
                **{
                    field: fake.random_element(options)
                    for field, options in facet_fields.items()
                },
            )
            item.authors = [
                LibraryItemAuthor(author=author)
                for author in self._authors(fake.random_int(1, 2))
            ]
            item.topics = [
                LibraryItemTopic(topic=topic) for topic in self._some(self.topics, 1, 3)
            ]
            item.tags.add(*self._tags())
            self._add(library_index, item)
        self._update(library_index, intro=self._intro())
        self.link_pages.append(library_index)

    def seed_magazine(self) -> None:
        magazine_index = MagazineIndexPage.objects.get()
        department_index = MagazineDepartmentIndexPage.objects.get()
        departments = [
            self._add(department_index, MagazineDepartmentFactory.build(title=title))
            for title in fake_content.MAGAZINE_DEPARTMENTS
        ]

        # Bimonthly issues back from this month: the newest fall inside the
        # subscriber-only window, the rest are public archive issues.
        first_of_month = self.today.replace(day=1)
        for number in range(self.scale.magazine_issues):
            issue = MagazineIssueFactory.build(
                publication_date=first_of_month - relativedelta(months=2 * number),
                issue_number=300 - number,
            )
            issue.cover_image = self._image(
                title=f"Western Friend: {issue.title}",
                alt_text=f"Cover of the {issue.publication_date:%B %Y} issue, “{issue.title}”",
                size=images.COVER_SIZE,
            )
            self._add(magazine_index, issue)

            article_count = fake.random_int(*self.scale.articles_per_issue)
            for position in range(article_count):
                # The newest issue's last article has a very long title.
                extra = (
                    {"title": fake_content.LONG_TITLE}
                    if number == 0 and position == article_count - 1
                    else {}
                )
                self._article(
                    issue,
                    departments,
                    is_featured=position == 0,
                    **extra,
                )
            if number == 0:
                # An unpublished article for testing drafts in the admin.
                self._article(issue, departments, live=False)

        self._update(department_index, intro=self._intro())
        self.link_pages.append(magazine_index)

    def _article(
        self,
        issue: Page,
        departments: list[Page],
        *,
        live: bool = True,
        **fields: Any,
    ) -> None:
        article = MagazineArticleFactory.build(
            department=fake.random_element(departments),
            **self._body_pools,
            **fields,
        )
        article.authors = [
            MagazineArticleAuthorFactory.build(author=author)
            for author in self._authors(fake.random_int(1, 2))
        ]
        article.tags.add(*self._tags())
        self._add(issue, article, live=live)

    def seed_deep_archive(self) -> None:
        magazine_index = MagazineIndexPage.objects.get()
        deep_archive = DeepArchiveIndexPage.objects.get()
        oldest = self.today.replace(year=1929, month=1, day=1)
        issues = []
        for number in range(self.scale.archive_issues):
            # One issue per year from 1929, in varying months.
            publication_date = oldest + relativedelta(years=number, months=number % 12)
            issue = ArchiveIssueFactory.build(
                publication_date=publication_date,
                internet_archive_identifier=f"friendsbulletin{publication_date:%Y%m}dev",
                western_friend_volume=f"Volume {number + 1}",
            )
            for archive_article in issue.archive_articles.all():
                archive_article.archive_authors = [
                    ArchiveArticleAuthorFactory.build(author=author)
                    for author in self._authors(1)
                ]
            issues.append(self._add(deep_archive, issue))
            self._count("archive articles", len(issue.archive_articles.all()))

        self._update(deep_archive, intro=self._intro())
        self._update(
            magazine_index,
            intro=self._intro(),
            deep_archive_intro=self._intro(),
            deep_archive_page=deep_archive,
            featured_deep_archive_issue=issues[0] if issues else None,
        )

    def seed_events(self) -> None:
        events_index = EventsIndexPage.objects.get()
        sponsors = self.meetings + self.organizations
        featured = 0
        for number in range(self.scale.events):
            # A third have ended and a quarter are other organizations'
            # events; the home page features upcoming Western events.
            past = _in_share(number, 1, 3)
            other_category = _in_share(number + 1, 1, 4)
            is_featured = not (past or other_category) and featured < FEATURED_EVENTS
            featured += is_featured
            event = EventFactory.build(
                past=past,
                other_category=other_category,
                is_featured=is_featured,
                **self._body_pools,
            )
            event.sponsors = [
                EventSponsor(sponsor=sponsor) for sponsor in self._some(sponsors, 1, 2)
            ]
            self._add(events_index, event)
        self._update(events_index, intro=self._intro())

    def seed_news(self) -> None:
        news_index = NewsIndexPage.objects.get()
        start_of_year = self.today.replace(month=1, day=1)
        for number in range(self.scale.news_items):
            # The news page shows the current year by default, so most items
            # land there; the rest fill the previous two years' filters.
            years_back = 0 if _in_share(number, 3, 5) else 1 + number % 2
            year_start = start_of_year - relativedelta(years=years_back)
            item = NewsItemFactory.build(
                publication_date=fake.date_between(
                    start_date=year_start,
                    end_date=min(
                        self.today,
                        year_start + relativedelta(months=12, days=-1),
                    ),
                ),
                **self._body_pools,
            )
            # The first item has no topic, for the "Uncategorized" group.
            if number:
                item.topics = [
                    NewsItemTopic(topic=topic)
                    for topic in self._some(self.topics, 1, 2)
                ]
            item.tags.add(*self._tags())
            # The second item is an unpublished draft.
            self._add(news_index, item, live=number != 1)
        self._update(news_index, intro=self._intro())
        self.link_pages.append(news_index)

    def seed_bookstore(self) -> None:
        product_index = ProductIndexPage.objects.get()
        books = []
        for number in range(self.scale.books):
            book = BookFactory.build(
                is_featured=number < FEATURED_BOOKS,
                sold_out=_in_share(number + 1, 1, 5),
            )
            book.image = self._image(
                title=book.title,
                alt_text=f"Front cover of the book {book.title}",
                size=images.PRODUCT_SIZE,
            )
            book.authors = [
                BookAuthorFactory.build(author=author)
                for author in self._authors(fake.random_int(1, 2))
            ]
            books.append(self._add(product_index, book))

        self._update(StoreIndexPage.objects.get(), intro=self._intro())

        for _ in range(self.scale.orders):
            # Marking the notification as sent stops paid orders emailing staff.
            order = OrderFactory.create(
                purchaser_email=fake.email(domain=fake_content.EMAIL_DOMAIN),
                recipient_address_country="United States",
                notification_sent_at=timezone.now(),
            )
            for book in self._some(books, 1, min(3, len(books))):
                OrderItemFactory.create(
                    order=order,
                    product_title=book.title,
                    product_id=book.pk,
                    price=book.price_usd,
                    quantity=fake.random_int(1, 4),
                )
            self._count("orders")

    def seed_documents(self) -> None:
        meeting_documents = MeetingDocumentIndexPage.objects.get()
        for _ in range(self.scale.meeting_documents):
            self._add(
                meeting_documents,
                MeetingDocumentFactory.build(
                    publishing_meeting=fake.random_element(self.meetings),
                    **self._body_pools,
                ),
            )
        self._update(meeting_documents, intro=self._intro())

        # Three years of documents in every board category.
        board_documents = PublicBoardDocumentIndexPage.objects.get()
        categories = PublicBoardDocument.PublicBoardDocmentCategoryChoices
        for category in categories:
            for years_back in range(3):
                publication_date = self.today - relativedelta(years=years_back)
                self._add(
                    board_documents,
                    PublicBoardDocumentFactory.build(
                        title=f"{category.label} {publication_date:%Y}",
                        category=category.value,
                        publication_date=publication_date,
                        **self._body_pools,
                    ),
                )
        self._update(board_documents, intro=self._intro())

    def seed_subscription_pages(self) -> None:
        plans = [
            ("P-DEV-DIGITAL", "Digital subscription", 30),
            ("P-DEV-PRINT", "Print and digital", 45),
            ("P-DEV-SUSTAINING", "Sustaining subscription", 100),
        ]
        self._update(
            SubscriptionIndexPage.objects.get(),
            intro=self._intro(),
            body=[
                {"type": "paragraph", "value": fake_content.paragraphs(2)},
                {
                    "type": "paypal_card_row",
                    "value": [
                        {
                            "type": "item",
                            "value": {
                                "paypal_plan_id": plan_id,
                                "paypal_plan_name": name,
                                "paypal_plan_price": price,
                            },
                        }
                        for plan_id, name, price in plans
                    ],
                },
            ],
        )
        self._update(ManageSubscriptionPage.objects.get(), intro=self._intro())

    def seed_home_page(self) -> None:
        home = HomePage.objects.get()
        community = CommunityPage.objects.get()
        sections = [
            MagazineIndexPage.objects.get(),
            EventsIndexPage.objects.get(),
            LibraryIndexPage.objects.get(),
            StoreIndexPage.objects.get(),
            NewsIndexPage.objects.get(),
            community,
        ]
        self._update(home, intro=fake_content.rich_text(sections))

        directory_pages = [
            MeetingIndexPage.objects.get(),
            OrganizationIndexPage.objects.get(),
            PersonIndexPage.objects.get(),
            OnlineWorshipIndexPage.objects.get(),
            MemorialIndexPage.objects.get(),
            CommunityDirectoryIndexPage.objects.get(),
        ]
        body = [
            fake_content.heading_block("Find Friends near you"),
            fake_content.rich_text_block(fake_content.paragraphs(2)),
            {
                "type": "card_row",
                "value": [
                    {
                        "type": "item",
                        "value": {"page": page.pk, "text": fake.sentence(nb_words=8)},
                    }
                    for page in directory_pages
                ],
            },
            {"type": "spacer", "value": {"height": "1.5"}},
            {
                "type": "card",
                "value": {
                    "title": "Share news from your meeting",
                    "text": fake_content.paragraphs(1),
                    "image": self.illustrations[0].pk if self.illustrations else None,
                    "image_align": "right",
                    "button": {
                        "button_text": "Read the latest news",
                        "page_link": NewsIndexPage.objects.get().pk,
                    },
                },
            },
        ]
        self._update(community, body=body)
