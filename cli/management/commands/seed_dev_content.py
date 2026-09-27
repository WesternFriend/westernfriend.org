from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from wagtail.images import get_image_model
from wagtail.models import Page, Revision, Site

from cli.dev_content.images import COLLECTION_NAME
from cli.dev_content.seeder import (
    DEV_PASSWORD,
    DEV_USERS,
    SCALES,
    DevContentSeeder,
)
from common.fake_content import EMAIL_DOMAIN
from home.models import HomePage


class Command(BaseCommand):
    help = (
        "Fill a development database with a complete mock website: contacts, "
        "meetings, magazine issues and articles, library, events, news, "
        "bookstore, documents, memorials, and user accounts."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--scale",
            choices=list(SCALES),
            default="medium",
            help="How much content to create (default: medium).",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=1234,
            help="Random seed; the same seed builds the same site (default: 1234).",
        )
        parser.add_argument(
            "--no-images",
            action="store_true",
            help="Skip generating placeholder cover, product, and body images.",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete the existing page tree and seeded accounts first.",
        )

    def handle(self, *args: tuple, **options: dict) -> None:
        self._check_environment()

        with transaction.atomic():
            if options["reset"]:
                self.stdout.write("Deleting existing content...")
                delete_content()
            elif has_content():
                message = (
                    "The database already has content. Run with --reset to "
                    "replace it with freshly seeded content."
                )
                raise CommandError(message)

            if not HomePage.objects.exists():
                self.stdout.write("Scaffolding the initial site structure...")
                call_command("scaffold_initial_content", stdout=self.stdout)

            seeder = DevContentSeeder(
                scale=SCALES[str(options["scale"])],
                seed=int(options["seed"]),  # type: ignore[call-overload]
                with_images=not options["no_images"],
                log=self.stdout.write,
            )
            counts = seeder.run()

        self._report(counts)

    def _check_environment(self) -> None:
        # Seeding publishes pages, and publishing purges the frontend cache.
        if getattr(settings, "WAGTAILFRONTENDCACHE", None):
            message = (
                "A frontend cache (Cloudflare) is configured, so this looks "
                "like a live site. Unset CLOUDFLARE_API_TOKEN to seed content."
            )
            raise CommandError(message)
        # There's deliberately no override: seeding creates a superuser with
        # a password published in this repository.
        if not settings.DEBUG:
            message = (
                "DEBUG is off, so this may be a live site. Set "
                "DJANGO_DEBUG=true for local development."
            )
            raise CommandError(message)

    def _report(self, counts: dict[str, int]) -> None:
        self.stdout.write("")
        for label, count in sorted(counts.items()):
            self.stdout.write(f"  {count:>5}  {label}")
        self.stdout.write("")
        self.stdout.write(
            f"Dev accounts (password {DEV_PASSWORD!r}): "
            + ", ".join(DEV_USERS.values()),
        )
        self.stdout.write(self.style.SUCCESS("Development content is ready."))


def has_content() -> bool:
    """Whether the database holds anything beyond the scaffolded structure.

    The scaffold never creates revisions, so any revision means someone
    edited or seeded content. The scaffold's pages are one-per-site index
    pages plus the types below, so any other page means content was added
    some other way, such as an import.
    """
    from documents.models import MeetingDocumentIndexPage, PublicBoardDocumentIndexPage
    from wf_pages.models import WfPage

    scaffolded_types = {WfPage, MeetingDocumentIndexPage, PublicBoardDocumentIndexPage}

    if Revision.page_revisions.exists():
        return True

    content_types = ContentType.objects.filter(
        pk__in=Page.objects.filter(depth__gt=2).values("content_type"),
    )
    return any(
        page_class.max_count != 1 and page_class not in scaffolded_types
        for page_class in (content_type.model_class() for content_type in content_types)
    )


def delete_content() -> None:
    """Remove the page tree, seed images, and seed accounts.

    Memorials, meeting documents, and magazine articles hold PROTECT foreign
    keys to other pages, so they go first. Articles and archive issues must
    also go while their authors exist, because deleting an author link
    recalculates that author's publication statistics. The rest of the tree
    then cascades from the home page.
    """
    from django.contrib.auth import get_user_model

    from documents.models import MeetingDocument
    from magazine.models import ArchiveIssue, MagazineArticle
    from memorials.models import Memorial
    from orders.models import Order
    from subscription.models import Subscription

    for model in (Memorial, MeetingDocument, MagazineArticle, ArchiveIssue):
        for page in model.objects.all():
            page.delete()

    # Deleting a site's root page would delete the site with it.
    root = Page.get_first_root_node()
    Site.objects.filter(root_page__depth__gt=1).update(root_page=root)
    for home in HomePage.objects.all():
        home.delete()

    get_image_model().objects.filter(collection__name=COLLECTION_NAME).delete()
    Order.objects.filter(purchaser_email__endswith=f"@{EMAIL_DOMAIN}").delete()
    Subscription.objects.filter(user__email__in=DEV_USERS.values()).delete()
    get_user_model().objects.filter(email__in=DEV_USERS.values()).delete()
