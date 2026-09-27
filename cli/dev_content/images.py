"""Placeholder images for development content.

Images are drawn with Pillow rather than downloaded, so seeding works
offline and produces the same pictures for the same seed. Each one carries
alt text in the image description, as editors are asked to provide.
"""

from io import BytesIO
from typing import TYPE_CHECKING

from django.core.files.images import ImageFile
from django.utils.text import slugify
from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont
from wagtail.images import get_image_model
from wagtail.models import Collection

from common.fake_content import fake

if TYPE_CHECKING:
    from wagtail.images.models import AbstractImage

COLLECTION_NAME = "Development seed images"

# Muted earth tones, all dark enough for white text to pass WCAG AA.
PALETTE = ["#2f4858", "#33658a", "#55624c", "#6b4e71", "#7a4b3a", "#3d5a80", "#5c4d7d"]

# (width, height) for each use on the site.
COVER_SIZE = (600, 800)
PRODUCT_SIZE = (500, 750)
ILLUSTRATION_SIZE = (1200, 800)


def get_seed_collection() -> Collection:
    existing = Collection.objects.filter(name=COLLECTION_NAME).first()
    if existing:
        return existing
    return Collection.get_first_root_node().add_child(name=COLLECTION_NAME)


def _png(label: str, size: tuple[int, int], color: str) -> bytes:
    width, height = size
    image = PILImage.new("RGB", size, color)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=max(24, width // 14))

    # Wrap the label to roughly fit the image width.
    words, lines, line = label.split(), [], ""
    max_chars = max(10, width // (font.size // 2 + 4))
    for word in words:
        candidate = f"{line} {word}".strip()
        if len(candidate) > max_chars and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    lines.append(line)

    text = "\n".join(lines)
    draw.multiline_text(
        (width / 2, height / 2),
        text,
        fill="white",
        font=font,
        anchor="mm",
        align="center",
        spacing=font.size // 3,
    )
    draw.rectangle((16, 16, width - 16, height - 16), outline="white", width=4)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def create_image(
    *,
    title: str,
    alt_text: str,
    size: tuple[int, int],
    collection: Collection,
) -> "AbstractImage":
    image_model = get_image_model()
    content = _png(title, size, fake.random_element(PALETTE))
    image = image_model(
        title=title,
        description=alt_text,
        collection=collection,
        file=ImageFile(BytesIO(content), name=f"{slugify(title)[:80] or 'image'}.png"),
    )
    image.save()
    return image
