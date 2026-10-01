import shutil
import tempfile
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings, tag
from django.urls import reverse
from wagtail.images import get_image_model
from wagtail.models import Page, PageViewRestriction, Site

from cli.dev_content.images import get_seed_collection
from cli.dev_content.seeder import DEV_USERS, SCALES, DevContentSeeder
from cli.management.commands.seed_dev_content import delete_content, has_content
from contact.models import Meeting, Person
from events.factories import EventFactory
from home.models import HomePage
from magazine.models import ArchiveIssue, MagazineArticle, MagazineIssue
from orders.models import Order
from store.models import Book


def seed(**options) -> str:
    # Django runs tests with DEBUG off, which the command refuses.
    stdout = StringIO()
    with override_settings(DEBUG=True):
        call_command("seed_dev_content", scale="small", stdout=stdout, **options)
    return stdout.getvalue()


# Seeding takes several seconds, so these are tagged; CI runs them in their
# own job. Run them locally with `python manage.py test --tag seed`.
@tag("seed")
class SeedDevContentTest(TestCase):
    """Keep seed_dev_content working, then use its site as a smoke test.

    The first group of tests covers the command itself. The smoke tests
    below reuse the seeded site to check that every page and every page
    type's admin form renders with realistic data, which catches template
    errors no unit test reaches.
    """

    @classmethod
    def setUpClass(cls) -> None:
        # Keep generated images out of the real media folder. This runs
        # before super().setUpClass(), which seeds the site.
        media_root = tempfile.mkdtemp(prefix="seed-dev-content-")
        cls.addClassCleanup(shutil.rmtree, media_root, ignore_errors=True)
        cls.enterClassContext(override_settings(MEDIA_ROOT=media_root))
        super().setUpClass()

    @classmethod
    def setUpTestData(cls) -> None:
        cls.output = seed()

    def test_creates_every_section(self) -> None:
        scale = SCALES["small"]
        self.assertEqual(MagazineIssue.objects.count(), scale.magazine_issues)
        self.assertEqual(ArchiveIssue.objects.count(), scale.archive_issues)
        self.assertEqual(Book.objects.count(), scale.books)
        self.assertEqual(
            Meeting.objects.filter(meeting_type="yearly_meeting").count(),
            scale.yearly_meetings,
        )
        # Worship groups and monthly meetings nest under their parents.
        self.assertTrue(
            Meeting.objects.filter(
                meeting_type="monthly_meeting",
                depth__gt=5,
            ).exists(),
        )
        self.assertGreaterEqual(Person.objects.count(), scale.people)
        self.assertIn("Development content is ready.", self.output)

    def test_recent_articles_are_for_subscribers(self) -> None:
        """The seeded accounts and issue dates exercise the paywall."""
        newest_issue = MagazineIssue.objects.order_by("-publication_date").first()
        article = (
            MagazineArticle.objects.child_of(newest_issue)
            .live()
            .filter(is_featured=False)
            .first()
        )

        response = self.client.get(article.url)
        self.assertFalse(response.context["user_can_view_full_article"])

        subscriber = get_user_model().objects.get(email=DEV_USERS["subscriber"])
        self.client.force_login(subscriber)
        response = self.client.get(article.url)
        self.assertTrue(response.context["user_can_view_full_article"])

    def test_refuses_to_seed_twice_without_reset(self) -> None:
        with self.assertRaisesMessage(CommandError, "--reset"):
            seed()

    def test_reset_deletes_seeded_content(self) -> None:
        delete_content()

        self.assertFalse(HomePage.objects.exists())
        self.assertEqual(Page.objects.count(), 1)
        # The site survives, pointing at the root, ready to be scaffolded again.
        self.assertEqual(Site.objects.get().root_page, Page.get_first_root_node())
        self.assertFalse(
            get_user_model().objects.filter(email__in=DEV_USERS.values()).exists(),
        )
        self.assertFalse(get_image_model().objects.exists())
        self.assertFalse(Order.objects.exists())

    def test_reset_option_deletes_and_rescaffolds(self) -> None:
        # Stub out the seeder, so this checks the command's wiring without
        # seeding a second site.
        with patch(
            "cli.management.commands.seed_dev_content.DevContentSeeder",
        ) as seeder_class:
            seeder_class.return_value.run.return_value = {}
            output = seed(reset=True)

        self.assertIn("Deleting existing content", output)
        self.assertTrue(HomePage.objects.exists())
        self.assertFalse(Person.objects.exists())

    def test_seeding_again_skips_existing_accounts(self) -> None:
        user_count = get_user_model().objects.count()
        seeder = DevContentSeeder(scale=SCALES["small"], seed=1, with_images=False)

        seeder.seed_users()

        self.assertEqual(get_user_model().objects.count(), user_count)
        self.assertNotIn("users", seeder.counts)

    def test_no_images_option_skips_images(self) -> None:
        seeder = DevContentSeeder(scale=SCALES["small"], seed=1, with_images=False)

        seeder.seed_images()

        self.assertEqual(seeder.illustrations, [])
        self.assertIsNone(seeder._image("Cover", "Alt text", (10, 10)))

    def test_seed_collection_is_reused(self) -> None:
        self.assertEqual(get_seed_collection(), get_seed_collection())

    def test_slugs_are_unique_among_siblings(self) -> None:
        seeder = DevContentSeeder(scale=SCALES["small"], seed=1, with_images=False)
        home_page = HomePage.objects.get()

        self.assertEqual(seeder._unique_slug(home_page, "Magazine"), "magazine-2")
        self.assertEqual(seeder._unique_slug(home_page, "Magazine"), "magazine-3")

    # Site smoke tests

    def test_every_live_page_renders(self) -> None:
        restricted_paths = [
            restriction.page.path for restriction in PageViewRestriction.objects.all()
        ]
        pages = Page.objects.live().filter(depth__gt=1).specific()
        self.assertGreater(pages.count(), 100)

        for page in pages:
            with self.subTest(page=page.url, type=type(page).__name__):
                response = self.client.get(page.url)
                if any(page.path.startswith(path) for path in restricted_paths):
                    self.assertEqual(response.status_code, 302)
                else:
                    self.assertEqual(response.status_code, 200)

    def test_admin_can_edit_each_page_type(self) -> None:
        admin = get_user_model().objects.get(email=DEV_USERS["admin"])
        self.client.force_login(admin)

        one_page_per_type = {}
        for page in Page.objects.filter(depth__gt=1).order_by("path"):
            one_page_per_type.setdefault(page.content_type_id, page)

        for page in one_page_per_type.values():
            with self.subTest(type=page.specific_class.__name__):
                response = self.client.get(
                    reverse("wagtailadmin_pages:edit", args=[page.pk]),
                )
                self.assertEqual(response.status_code, 200)

    def test_a11y_urls_covers_every_page_type(self) -> None:
        """The accessibility check's URL list resolves on a seeded site.

        CI scans exactly these URLs (docs/accessibility-checks.md), so each
        must come back and each must serve a page.
        """
        stdout = StringIO()
        call_command("a11y_urls", base="", stdout=stdout)
        urls = stdout.getvalue().split()

        self.assertEqual(len(urls), 9)
        self.assertIn("/", urls)
        self.assertIn("/accounts/login/", urls)
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_a11y_search_url_returns_results(self) -> None:
        """The search scan must see result rows, not the empty state.

        The query is a word from a seeded article's title, because a fixed
        word can be a stopword the search view strips (as "the" was).
        """
        stdout = StringIO()
        call_command("a11y_urls", base="", stdout=stdout)
        search_url = next(
            url for url in stdout.getvalue().split() if url.startswith("/search/")
        )

        response = self.client.get(search_url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["paginated_search_results"].page.object_list)


class SeedDevContentGuardTest(TestCase):
    def setUp(self) -> None:
        call_command("scaffold_initial_content", stdout=StringIO())

    def test_scaffolded_site_has_no_content(self) -> None:
        self.assertFalse(has_content())

    def test_edited_pages_count_as_content(self) -> None:
        HomePage.objects.get().save_revision()

        self.assertTrue(has_content())

    def test_imported_pages_count_as_content(self) -> None:
        # Pages added without revisions, as the content importers do.
        EventFactory.create()

        self.assertTrue(has_content())

    @override_settings(DEBUG=True)
    def test_refuses_to_seed_a_site_with_content(self) -> None:
        EventFactory.create()

        with self.assertRaisesMessage(CommandError, "--reset"):
            call_command("seed_dev_content", scale="small", stdout=StringIO())

    def test_refuses_without_debug(self) -> None:
        with self.assertRaisesMessage(CommandError, "DEBUG is off"):
            call_command("seed_dev_content", scale="small", stdout=StringIO())

    @override_settings(DEBUG=True, WAGTAILFRONTENDCACHE={"cloudflare": {}})
    def test_refuses_when_frontend_cache_is_configured(self) -> None:
        with self.assertRaisesMessage(CommandError, "frontend cache"):
            call_command("seed_dev_content", scale="small", stdout=StringIO())


class A11yUrlsGuardTest(TestCase):
    """The URL command fails loudly rather than scanning fewer templates."""

    def test_refuses_when_a_page_type_is_missing(self) -> None:
        # An unseeded database has no magazine issue (nor anything else);
        # naming the missing type makes the CI failure self-explanatory.
        with self.assertRaisesMessage(CommandError, "magazine issue"):
            call_command("a11y_urls", stdout=StringIO())
