"""Print the URLs the automated accessibility check scans.

The list covers one live page of every major template the September 2026
audit called representative: home, a magazine issue, an article, a library
item, an event, a memorial, search results, subscribe, and login. pa11y-ci
reads these URLs (see .pa11yci and docs/accessibility-checks.md), so the CI
job scans whatever the seeded database actually contains instead of
hard-coding slugs the seeder might change.

The command fails if any page type has no live page: silently scanning fewer
templates would let a regression through while CI stays green.
"""

from django.core.management.base import BaseCommand, CommandError

from events.models import Event
from library.models import LibraryItem
from magazine.models import MagazineArticle, MagazineIssue
from memorials.models import Memorial
from subscription.models import SubscriptionIndexPage


class Command(BaseCommand):
    help = "Print representative page URLs for the accessibility check."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--base",
            default="http://127.0.0.1:8000",
            help="Base URL of the running server (default: %(default)s).",
        )

    def handle(self, *args: tuple, **options: dict) -> None:
        base = str(options["base"]).rstrip("/")

        pages = {
            "magazine issue": MagazineIssue,
            "magazine article": MagazineArticle,
            "library item": LibraryItem,
            "event": Event,
            "memorial": Memorial,
            "subscribe": SubscriptionIndexPage,
        }

        urls = ["/"]
        for label, model in pages.items():
            page = model.objects.live().public().first()
            if page is None or not page.url:
                message = (
                    f"No live {label} page found - seed the database first "
                    "(./manage.py seed_dev_content)."
                )
                raise CommandError(message)
            urls.append(page.url)

        # Search results exercise the result list and paginator templates;
        # "the" is guaranteed to match seeded content.
        urls.append("/search/?query=the")
        urls.append("/accounts/login/")

        for url in urls:
            self.stdout.write(f"{base}{url}")
