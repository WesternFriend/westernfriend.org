from django.core.management.base import BaseCommand
from wagtail.images import get_image_model


class Command(BaseCommand):
    help = (
        "List images saved without a description. Templates use the description "
        "as alt text and fall back to the title, so these images leave "
        "screen-reader users with filename-like alt text."
    )

    def handle(self, *args, **options):
        images = list(
            get_image_model()
            # Whitespace-only descriptions render as empty alt text too, so
            # match them along with the truly empty ones. The admin form now
            # prevents both, but images that predate it can hold either.
            .objects.filter(description__regex=r"^\s*$")
            .order_by("title")
            .only("title"),
        )

        count = len(images)
        if not count:
            self.stdout.write(
                self.style.SUCCESS("Every image has a description."),
            )
            return

        for image in images:
            self.stdout.write(f"{image.pk}\t{image.title}")

        self.stdout.write(
            self.style.WARNING(
                f"{count} image(s) have no description. "
                "Editing one in the admin will now ask for it.",
            ),
        )
