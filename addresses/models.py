from django.db import models
from wagtail.admin.panels import FieldPanel


class Address(models.Model):
    """Model representing a street or post office address.

    Properties are modelled after Microformats specification.
    http://microformats.org/wiki/adr
    """

    class AddressTypeChoices(models.TextChoices):
        """Choices for the type of address."""

        MAILING = "mailing", "Mailing"
        WORSHIP = "worship", "Worship"

    street_address = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )
    extended_address = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )
    po_box_number = models.CharField(
        max_length=32,
        blank=True,
        default="",
        help_text="P.O. Box, if relevant",
    )
    locality = models.CharField(
        max_length=255,
        help_text="Locality or city",
        null=True,
        blank=True,
    )
    region = models.CharField(
        max_length=255,
        help_text="State or region",
        blank=True,
        default="",
    )
    postal_code = models.CharField(
        max_length=16,
        help_text="Postal code (or zipcode)",
        null=True,
        blank=True,
    )
    country = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    address_type = models.CharField(
        max_length=255,
        choices=AddressTypeChoices.choices,
    )
    latitude = models.FloatField(
        null=True,
        blank=True,
    )
    longitude = models.FloatField(
        null=True,
        blank=True,
    )

    panels = [
        FieldPanel("address_type"),
        FieldPanel("street_address"),
        FieldPanel("extended_address"),
        FieldPanel("po_box_number"),
        FieldPanel("locality"),
        FieldPanel("region"),
        FieldPanel("postal_code"),
        FieldPanel("country"),
        FieldPanel("latitude"),
        FieldPanel("longitude"),
    ]

    def __str__(self) -> str:
        """Return a string representation of the address."""

        address_string = ""

        # construct an address components list
        address_components: list[str | None] = [
            self.street_address,
            self.extended_address,
            self.locality,
            self.region,
            self.postal_code,
            self.country,
        ]

        # filter out empty components
        filtered_address_components = list(
            filter(lambda x: x is not None and x != "", address_components)
        )

        # if the filtered components list isn't empty
        # join the components into a string separated by commas
        if filtered_address_components:
            address_string = ", ".join(filtered_address_components)  # type: ignore

        return address_string

    class Meta:
        abstract = True
