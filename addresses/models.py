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
        default="United States",
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

        # Construct the address string using
        # street_address, locality, region, and country
        # adding commas and spaces as needed
        # e.g. 123 Main St, Anytown, CA, 12345, United States
        address_string = ""
        if self.street_address != "":
            address_string += f"{ self.street_address }, "
        if self.locality != "":
            address_string += f"{ self.locality }, "
        if self.region != "":
            address_string += f"{ self.region }, "
        if self.postal_code != "":
            address_string += f"{ self.postal_code }, "
        if self.country != "":
            address_string += f"{ self.country }"

        return address_string

    class Meta:
        abstract = True
