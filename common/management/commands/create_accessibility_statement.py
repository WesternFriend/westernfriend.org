"""Create the accessibility statement page as an unpublished draft.

The footer links to a live, public page with the slug ``accessibility`` (see
``common.templatetags.common_tags.live_page_url_by_slug``). This command creates
that page, pre-filled with the draft wording from
``docs/accessibility-statement.md``, so an editor only has to review it and
press Publish rather than build it from scratch and work out the page type.

It deliberately leaves the page **unpublished**: the text makes a public WCAG
2.2 AA conformance claim on Western Friend's behalf, and a person has to stand
behind it (and set the review date) before it goes live.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from wagtail.models import Site
from wagtail.rich_text import RichText

from wf_pages.models import WfPage

STATEMENT_SLUG = "accessibility"
STATEMENT_TITLE = "Accessibility"

# Each ("heading", text) entry becomes a level-2 "heading" block and each
# ("rich_text", html) entry a "rich_text" block in the page body. The section
# titles are heading blocks, not bold paragraphs: a bold paragraph reads as
# plain text to a screen reader, so the statement could not be navigated by
# heading — and the body's rich text has no heading feature, so real headings
# have to be their own blocks. Kept in sync with the draft in
# docs/accessibility-statement.md; the editor refines it before publishing.
BODY_BLOCKS = [
    (
        "rich_text",
        "<p>Western Friend wants everyone to be able to read what we publish, "
        "including people who use screen readers, keyboards, magnification, or "
        "speech input.</p>",
    ),
    ("heading", "What we aim for"),
    (
        "rich_text",
        "<p>We aim to meet the Web Content Accessibility Guidelines (WCAG) 2.2 "
        "at level AA across westernfriend.org.</p>",
    ),
    ("heading", "Where we currently fall short"),
    (
        "rich_text",
        "<p>We had the site reviewed in September 2026. These are the problems "
        "we know about and have not yet fixed:</p>"
        "<ul>"
        "<li><b>Audio and video have no captions or transcripts.</b> Podcasts "
        "and uploaded video are published without them. Where a video is hosted "
        "on YouTube or Vimeo, any captions are the ones that service provides.</li>"
        "<li><b>Some embedded material is outside our control.</b> The Internet "
        "Archive reader and the PayPal payment buttons come from other "
        "organisations, and we cannot change how they behave with assistive "
        "technology. If one of them blocks you, write to us and we will get you "
        "what you need another way.</li>"
        "<li><b>Our testing has limits.</b> The review used automated checks and "
        "keyboard testing. We have not yet done a full pass with a screen "
        "reader, so there will be problems we have not found. Please tell us "
        "about them.</li>"
        "</ul>",
    ),
    ("heading", "Telling us about a problem"),
    (
        "rich_text",
        "<p>If something on this site stops you reading it, please write to "
        '<a href="mailto:editor@westernfriend.org">editor@westernfriend.org</a> '
        "or call (503) 487-2945. Tell us the page and what happened, and we will "
        "reply and say what we can do.</p>"
        "<p>If you need an article in another form, ask, and we will send it to "
        "you.</p>",
    ),
    ("heading", "This statement"),
    (
        "rich_text",
        "<p>This is a draft awaiting editorial review. Confirm the wording is "
        "true, then set the date you publish it.</p>",
    ),
]


def _block_value(block_type: str, value: str) -> dict | RichText:
    """Turn a BODY_BLOCKS entry into its StreamField block value.

    The page title is the page's single h1, so every section heading sits one
    level below it at h2.
    """
    if block_type == "heading":
        return {"heading_level": "h2", "heading_text": value, "target_slug": ""}
    return RichText(value)


class Command(BaseCommand):
    help = "Create the accessibility statement as an unpublished draft page."

    @transaction.atomic
    def handle(self, *args: tuple, **options: dict) -> None:
        site = (
            Site.objects.filter(is_default_site=True).first() or Site.objects.first()
        )
        if site is None:
            message = "No Wagtail site is configured to attach the page to."
            raise CommandError(message)

        home = site.root_page
        existing = home.get_children().filter(slug=STATEMENT_SLUG).first()
        if existing is not None:
            state = "live" if existing.live else "a draft"
            self.stdout.write(
                f'A page with slug "{STATEMENT_SLUG}" already exists under '
                f'"{home.title}" ({state}); leaving it untouched.'
            )
            return

        page = WfPage(
            title=STATEMENT_TITLE,
            slug=STATEMENT_SLUG,
            body=[
                (block_type, _block_value(block_type, value))
                for block_type, value in BODY_BLOCKS
            ],
            # A draft: it must be reviewed and published by a person.
            live=False,
            has_unpublished_changes=True,
        )
        home.add_child(instance=page)
        page.save_revision()

        self.stdout.write(
            self.style.SUCCESS(
                f'Created "{STATEMENT_TITLE}" as an unpublished draft under '
                f'"{home.title}". Review it in the Wagtail admin and publish it '
                "when the wording is true; the footer link appears once it is live."
            )
        )
