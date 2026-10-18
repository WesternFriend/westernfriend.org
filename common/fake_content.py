"""Vocabulary and body builders for mock content.

Factories use these for their Faker-driven defaults, and the development
seeder (``manage.py seed_dev_content``) uses the vocabulary for site
structure. Faker supplies names, places, and filler prose; the lists below
give titles and taxonomy terms a recognisable Western Friend flavour, so
seeded pages read like the real thing during UX reviews.

``fake`` shares Faker's global random generator, which
``factory.random.reseed_random()`` seeds, so one seed controls every value.
"""

from typing import TYPE_CHECKING

from django.utils.html import escape
from faker import Faker

if TYPE_CHECKING:
    from wagtail.images.models import Image
    from wagtail.models import Page

fake = Faker("en_US")

# Mock email addresses use a reserved domain that can never receive mail.
EMAIL_DOMAIN = "example.com"

AUDIENCES = [
    "Adults",
    "Young Adult Friends",
    "Youth",
    "Children",
    "Families",
    "Educators",
]

GENRES = [
    "Essay",
    "Poetry",
    "Memoir",
    "History",
    "Epistle",
    "Sermon",
    "Interview",
    "Fiction",
    "Study Guide",
]

MEDIA = ["Article", "Audio", "Video", "Book", "Pamphlet", "Podcast", "Slideshow"]

TIME_PERIODS = [
    "1600s",
    "1700s",
    "1800s",
    "Early 1900s",
    "Mid 1900s",
    "Late 1900s",
    "2000s",
    "2010s",
    "2020s",
]

TOPICS = [
    "Peace",
    "Simplicity",
    "Integrity",
    "Community",
    "Equality",
    "Stewardship",
    "Worship",
    "Discernment",
    "Racial Justice",
    "Earthcare",
    "Prison Ministry",
    "Spiritual Formation",
    "Quaker History",
    "Leadings",
    "Clearness",
    "Hospitality",
]

TAGS = [
    "vocal ministry",
    "silence",
    "testimonies",
    "outreach",
    "youth programs",
    "elders",
    "yearly meeting",
    "climate",
    "migration",
    "nonviolence",
    "gardening",
    "grief",
    "music",
    "art",
]

MAGAZINE_DEPARTMENTS = [
    "Editor's Notes",
    "Features",
    "Poetry",
    "Letters",
    "Book Reviews",
    "Milestones",
    "Among Friends",
    "Young Friends",
    "Quaker Profiles",
    "Faith and Practice",
]

ISSUE_THEMES = [
    "Silence",
    "Stewardship of the Earth",
    "Money",
    "Leadings",
    "Hope",
    "Waiting",
    "Home",
    "Borders",
    "Truth",
    "Aging",
    "Joy",
    "Community",
    "Wilderness",
    "Listening",
    "Courage",
    "Healing",
    "Service",
    "Wonder",
    "Tenderness",
    "Endurance",
]

ORGANIZATION_KINDS = ["Committee", "Service", "Fellowship", "Center", "School"]

YEARLY_MEETING_REGIONS = [
    "Cascadia",
    "High Desert",
    "Sierra Coast",
    "Great Basin",
    "Rocky Mountain",
]

BOOK_TITLE_PATTERNS = [
    "Walking in the {noun}",
    "The {adjective} Meeting",
    "Letters from the {noun}",
    "A {adjective} Testimony",
    "Listening for the {noun}",
    "Faith and {noun}",
]

TITLE_NOUNS = [
    "Light",
    "Silence",
    "Wilderness",
    "Seed",
    "Spirit",
    "Harvest",
    "River",
    "Threshold",
    "Garden",
    "Journey",
]

TITLE_ADJECTIVES = [
    "Gathered",
    "Quiet",
    "Living",
    "Patient",
    "Faithful",
    "Open",
    "Tender",
    "Plain",
]

WESTERN_TIMEZONES = [
    "America/Los_Angeles",
    "America/Denver",
    "America/Phoenix",
    "America/Anchorage",
    "Pacific/Honolulu",
]

EVENT_KINDS = [
    "Gathering",
    "Retreat",
    "Workshop",
    "Worship Sharing",
    "Book Discussion",
    "Annual Session",
]

# A deliberately long title and non-ASCII names catch truncation, wrapping,
# and encoding problems that tidy Faker output never exercises.
LONG_TITLE = (
    "On the Practice of Waiting Worship in a Distracted Age: Reflections "
    "Gathered from Three Generations of Friends Across the Western United States"
)
INTERNATIONAL_NAMES = [
    ("Zoë", "Ñúñez-Øberg"),
    ("Nguyễn", "Thị Minh"),
    ("Siobhán", "Ó Briain"),
    ("José", "Muñoz"),
]


def book_title() -> str:
    pattern = fake.random_element(BOOK_TITLE_PATTERNS)
    return pattern.format(
        noun=fake.random_element(TITLE_NOUNS),
        adjective=fake.random_element(TITLE_ADJECTIVES),
    )


def headline() -> str:
    """A title-cased headline without Faker's trailing period."""
    return fake.sentence(nb_words=fake.random_int(3, 7)).rstrip(".").title()


def paragraphs(count: int = 1) -> str:
    return "".join(
        f"<p>{escape(fake.paragraph(nb_sentences=5))}</p>" for _ in range(count)
    )


def rich_text(link_pages: "list[Page] | None" = None) -> str:
    """Rich text HTML using the editor features that need no uploads or network.

    That's every feature COMMON_STREAMFIELD_BLOCKS enables except document
    links and embeds.
    """
    html = [paragraphs(2)]

    items = "".join(f"<li>{escape(fake.sentence())}</li>" for _ in range(3))
    html.append(f"<ul>{items}</ul>" if fake.boolean() else f"<ol>{items}</ol>")

    sentence = escape(fake.sentence(nb_words=10))
    html.append(
        f"<p><b>{escape(fake.word().title())}.</b> <i>{sentence}</i> "
        f'Read more at <a href="https://example.com/{fake.slug()}">'
        f"{escape(fake.catch_phrase())}</a>.</p>",
    )

    if link_pages:
        page = fake.random_element(link_pages)
        html.append(
            f'<p>See also <a linktype="page" id="{page.pk}">{escape(page.title)}</a>.</p>',
        )

    html.append("<hr/>")
    html.append(
        f"<p>{escape(fake.sentence(nb_words=6))} "
        f"<s>{escape(fake.word())}</s> {escape(fake.word())}"
        f"<sup>{fake.random_int(1, 9)}</sup></p>",
    )
    html.append(f"<blockquote>{escape(fake.paragraph(nb_sentences=2))}</blockquote>")
    return "".join(html)


def _block(block_type: str, value: object) -> dict:
    return {"type": block_type, "value": value, "id": fake.uuid4()}


def heading_block(text: str, level: str = "h2") -> dict:
    return _block(
        "heading",
        {"heading_level": level, "heading_text": text, "target_slug": ""},
    )


def rich_text_block(html: str) -> dict:
    return _block("rich_text", html)


def image_block(image: "Image") -> dict:
    return _block(
        "image",
        {
            "image": image.pk,
            "caption": fake.sentence(nb_words=6),
            "width": 800,
            "align": fake.random_element(["", "left", "right"]),
            "link": "",
        },
    )


def stream_body(
    *,
    images: "list[Image] | None" = None,
    link_pages: "list[Page] | None" = None,
    sections: int = 3,
) -> list[dict]:
    """StreamField data for COMMON_STREAMFIELD_BLOCKS.

    Every body gets headings at two levels and rich text; pull quotes,
    spacers, preformatted text, and images are sprinkled in so each block
    template renders somewhere on the site. Embed and document blocks are
    skipped because they need network access or uploaded files.
    """
    blocks = [rich_text_block(paragraphs(1))]

    for section in range(sections):
        blocks.append(heading_block(headline()))
        blocks.append(rich_text_block(rich_text(link_pages)))

        if section == 0:
            blocks.append(_block("pullquote", fake.sentence(nb_words=14)))
        if images and fake.boolean(chance_of_getting_true=60):
            blocks.append(image_block(fake.random_element(images)))
        if fake.boolean(chance_of_getting_true=40):
            blocks.append(heading_block(headline(), level="h3"))
            blocks.append(rich_text_block(paragraphs(1)))

    if fake.boolean(chance_of_getting_true=25):
        blocks.append(_block("spacer", {"height": "2.0"}))
        verse = "\n".join(fake.sentence(nb_words=5) for _ in range(4))
        blocks.append(_block("preformatted_text", verse))

    return blocks
